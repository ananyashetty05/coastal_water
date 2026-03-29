import streamlit as st
import pandas as pd

from core.classifier import benchmark_models
from core.state import get_df, get_ml_bundle, set_ml_bundle
from core.predictor import predict
from core.processor import (
    filter_df, get_countries, get_waterbody_types, METRIC_LABELS
)
from components.quality_badge import render as render_badge

st.set_page_config(page_title="Predictions · CoastalWatch", layout="wide")
st.title("🔮 7-Day Water Quality Forecast")
st.caption(
    "Linear-regression forecasts for CCME score and individual parameters. "
    "Row colours reflect projected quality category."
)

df = get_df()
if df is None:
    st.warning("⚠️ No data loaded. Please go to **Upload Data** first.")
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    sel_country = st.selectbox("Country", ["All"] + get_countries(df))
    sel_wbt     = st.selectbox("Waterbody Type", ["All"] + get_waterbody_types(df))

filtered_df = filter_df(
    df,
    country=None if sel_country == "All" else sel_country,
    waterbody_type=None if sel_wbt == "All" else sel_wbt,
)

locations = sorted(filtered_df["location"].unique())
if not locations:
    st.warning("No locations match filters.")
    st.stop()

location = st.selectbox("Select monitoring station", locations)

# Reuse cached classifier benchmark if available.
ml_bundle = get_ml_bundle()
if ml_bundle is None:
    try:
        ml_bundle = benchmark_models(df)
        set_ml_bundle(ml_bundle)
    except Exception:
        ml_bundle = None

# ── Run forecast ──────────────────────────────────────────────────────────────
with st.spinner("Running forecast model…"):
    try:
        result = predict(filtered_df, location, classifier_bundle=ml_bundle)
    except Exception as e:
        st.error(f"Forecast failed: {e}")
        st.stop()

predictions    = result["predictions"]     # dict: metric → list[float] (7 values)
forecast_series = result["forecast_series"] # dict: metric → pd.DataFrame (Historical + Forecast cols)
if result.get("best_model_name"):
    st.caption(f"Classification backend: `{result['best_model_name']}`")

# ── CCME projected badge ──────────────────────────────────────────────────────
day7_ccme = predictions.get("ccme_values", [None] * 7)[-1]

def _ccme_to_label(score) -> str:
    if score is None:
        return "Unknown"
    if score >= 95:  return "Excellent"
    if score >= 80:  return "Good"
    if score >= 65:  return "Marginal"
    if score >= 45:  return "Fair"
    return "Poor"

proj_label = _ccme_to_label(day7_ccme)
st.markdown("#### Projected Quality — Day 7")
render_badge({
    "status":   proj_label,
    "score":    round(day7_ccme, 2) if day7_ccme is not None else None,
    "messages": [f"Forecast CCME score: {day7_ccme:.1f}" if day7_ccme is not None else "No CCME data"],
})

# ── Day-by-day table ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📅 Day-by-Day Parameter Forecast")

# Build table: rows = Day+1…+7, cols = metrics
table_data = {
    METRIC_LABELS.get(m, m): [round(v, 3) for v in vals]
    for m, vals in predictions.items()
}
forecast_df = pd.DataFrame(table_data, index=[f"Day +{i+1}" for i in range(7)])

def _row_quality_style(row):
    """Colour each row by projected CCME WQI label."""
    ccme_col = METRIC_LABELS.get("ccme_values", "CCME Score")
    if ccme_col in row:
        label = _ccme_to_label(row[ccme_col])
    else:
        label = "Unknown"
    bg = {
        "Excellent": "#d4edda",
        "Good":      "#e8f5d4",
        "Marginal":  "#fff9c4",
        "Fair":      "#fde8d8",
        "Poor":      "#fde8e8",
    }.get(label, "")
    return [f"background-color:{bg}; color:#000000" for _ in row]

styled = (
    forecast_df.style
    .apply(_row_quality_style, axis=1)
    .set_properties(**{"color": "#000000"})
    .set_table_styles(
        [
            {"selector": "th", "props": [("color", "#000000")]},
            {"selector": "td", "props": [("color", "#000000")]},
        ]
    )
    .format("{:.3f}")
)
st.dataframe(styled, width="stretch")

# ── Forecast chart ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📈 Historical + Forecast Trend")

plot_metrics = {k: v for k, v in METRIC_LABELS.items() if k in forecast_series}
metric_choice = st.selectbox(
    "Select parameter to plot",
    list(plot_metrics.keys()),
    format_func=lambda k: plot_metrics[k],
)

if metric_choice in forecast_series:
    series_data = forecast_series[metric_choice]  # DataFrame with Historical / Forecast columns
    st.line_chart(series_data, width="stretch", height=340)
    st.caption(
        "**Historical** (solid) = actual observations · "
        "**Forecast** (lighter) = 7-day OLS regression projection."
    )
else:
    st.info("No forecast series available for this parameter.")

# ── Model explanation ─────────────────────────────────────────────────────────
with st.expander("ℹ️ About the forecast model"):
    st.markdown(
        """
        **Method**: Ordinary Least Squares (OLS) linear regression fitted on all
        available observations for the selected station.

        **Parameters forecast**: Dissolved Oxygen, pH, Ammonia, BOD, Orthophosphate,
        Temperature, Nitrogen, Nitrate, CCME Score.

        **Horizon**: 7 daily point estimates per parameter.

        **Limitations**:
        - Linear models cannot capture seasonal cycles or pollution events.
        - Accuracy degrades significantly beyond 3–4 days.
        - Stations with very few readings may produce unreliable forecasts.
        - Predictions are clipped to physically plausible ranges.

        For regulatory decisions, always use on-site measurements.
        """
    )
