import streamlit as st
import pandas as pd

from core.state import get_df
from core.processor import (
    get_stats, get_timeseries, get_wqi_distribution,
    filter_df, get_countries, get_waterbody_types,
    METRIC_LABELS, WQI_ORDER,
)
from components.metric_row import render as render_metrics
from components.quality_badge import render as render_badge
from components.summary_table import render as render_table

st.set_page_config(page_title="Analytics · CoastalWatch", layout="wide")
st.title("📊 Water Quality Analytics")
st.caption("Parameter trends, CCME scores, and quality breakdown by monitoring station.")

df = get_df()
if df is None:
    st.warning("⚠️ No data loaded. Please go to **Upload Data** first.")
    st.stop()

# ── Global filters (sidebar) ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    countries = get_countries(df)
    sel_country = st.selectbox("Country", ["All"] + countries)

    wbt_types = get_waterbody_types(df)
    sel_wbt   = st.selectbox("Waterbody Type", ["All"] + wbt_types)

filtered_df = filter_df(
    df,
    country=None if sel_country == "All" else sel_country,
    waterbody_type=None if sel_wbt == "All" else sel_wbt,
)

# ── Location selector (dropdown only) ────────────────────────────────────────
locations = sorted(filtered_df["location"].unique())
if not locations:
    st.warning("No locations match the current filters.")
    st.stop()

if "selected_location" not in st.session_state or st.session_state["selected_location"] not in locations:
    st.session_state["selected_location"] = locations[0]

st.markdown("**Select monitoring station**")
default_station = st.session_state.get("selected_location", locations[0])
default_idx = locations.index(default_station) if default_station in locations else 0
location = st.selectbox("Station", locations, index=default_idx, key="analytics_station_select")
st.session_state["selected_location"] = location

stats = get_stats(filtered_df, location)
if not stats:
    st.error("No data available for the selected location.")
    st.stop()

meta = stats.get("_meta", {})

# ── Station info banner ───────────────────────────────────────────────────────
st.markdown(
    f"""<div style="background:#f0f7ff;border:1px solid #d0e8ff;border-radius:10px;
        padding:.8rem 1.2rem;margin-bottom:.8rem;font-size:.9rem;color:#1a3a5c;">
        📍 <b>{meta.get('location','')}</b> &nbsp;·&nbsp;
        🌍 {meta.get('country','')} &nbsp;·&nbsp;
        💧 {meta.get('waterbody_type','')} &nbsp;·&nbsp;
        📋 {meta.get('n', 0):,} records
        ({meta.get('date_from','')} → {meta.get('date_to','')})
    </div>""",
    unsafe_allow_html=True,
)

# ── CCME quality badge ────────────────────────────────────────────────────────
render_badge({
    "status":   meta.get("ccme_wqi", "Unknown"),
    "score":    meta.get("ccme_values"),
    "messages": [],
})

st.markdown("#### Latest Parameter Readings")
render_metrics(stats)

st.markdown("---")

# ── Trend + Distribution charts ───────────────────────────────────────────────
left, right = st.columns(2, gap="large")

PLOTTABLE = {k: v for k, v in METRIC_LABELS.items() if k in stats}

with left:
    st.subheader("📈 Trend Over Time")
    trend_metric = st.selectbox(
        "Parameter", list(PLOTTABLE.keys()),
        format_func=lambda k: PLOTTABLE[k],
        key="trend_metric",
    )
    ts = get_timeseries(filtered_df, location, trend_metric)
    st.line_chart(ts.rename(PLOTTABLE[trend_metric]), width="stretch", height=280)

    slope = stats[trend_metric]["trend"]
    direction = "↑ Rising" if slope > 1e-6 else ("↓ Falling" if slope < -1e-6 else "→ Stable")
    st.caption(f"90-day trend: **{direction}** ({slope:+.5f} units/day)")

with right:
    st.subheader("📊 Monthly Averages")
    bar_metric = st.selectbox(
        "Parameter", list(PLOTTABLE.keys()),
        format_func=lambda k: PLOTTABLE[k],
        key="bar_metric",
    )
    ts_bar = get_timeseries(filtered_df, location, bar_metric)
    monthly = ts_bar.resample("ME").mean().rename(PLOTTABLE[bar_metric])
    st.bar_chart(monthly, width="stretch", height=280)
    st.caption("Each bar = monthly mean")

# ── CCME WQI breakdown for this location ─────────────────────────────────────
st.markdown("---")
wqi_col, params_col = st.columns(2, gap="large")

with wqi_col:
    st.subheader("🏷️ CCME WQI History")
    loc_df = filtered_df[filtered_df["location"] == location].copy()
    wqi_dist = get_wqi_distribution(filtered_df, location)
    wqi_colors_hex = {
        "Excellent": "#1a9850",
        "Good":      "#91cf60",
        "Marginal":  "#fee08b",
        "Fair":      "#fc8d59",
        "Poor":      "#d73027",
    }
    for label, count in wqi_dist.items():
        total = wqi_dist.sum()
        pct   = count / total * 100 if total else 0
        bar_w = max(int(pct * 2), 4)  # scale to ~200px max
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:.6rem;margin-bottom:.4rem;'>"
            f"<span style='width:80px;font-size:.85rem;'>{label}</span>"
            f"<div style='background:{wqi_colors_hex.get(label,'#aaa')};"
            f"width:{bar_w}px;height:18px;border-radius:4px;'></div>"
            f"<span style='font-size:.82rem;color:#555;'>{count} ({pct:.1f}%)</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # CCME score over time
    ccme_ts = get_timeseries(filtered_df, location, "ccme_values")
    if not ccme_ts.empty:
        st.line_chart(ccme_ts.rename("CCME Score"), width="stretch", height=200)

with params_col:
    st.subheader("🔎 All Parameters (normalised)")
    all_ts = pd.DataFrame(
        {METRIC_LABELS[m]: get_timeseries(filtered_df, location, m)
         for m in METRIC_LABELS if m in stats and m != "ccme_values"}
    )
    norm = (all_ts - all_ts.min()) / (all_ts.max() - all_ts.min() + 1e-9)
    norm.columns = [f"{c} (norm.)" for c in norm.columns]
    st.line_chart(norm, width="stretch", height=300)
    st.caption("All parameters normalised 0–1 for visual comparison.")

# ── Year-wise summary ────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Year-wise Summary")

from core.processor import METRICS, METRIC_LABELS as ML

loc_df = filtered_df[filtered_df["location"] == location].copy()
loc_df["year"] = loc_df["date"].dt.year

year_rows = []
for year, grp in loc_df.groupby("year"):
    row = {"Year": int(year), "Records": len(grp)}
    for m in METRICS:
        col = grp[m].dropna()
        if not col.empty:
            row[ML.get(m, m)] = round(float(col.mean()), 2)
        else:
            row[ML.get(m, m)] = None
    # CCME WQI most common label
    if "ccme_wqi" in grp.columns:
        row["CCME WQI"] = grp["ccme_wqi"].mode().iloc[0] if not grp["ccme_wqi"].dropna().empty else "—"
    year_rows.append(row)

if year_rows:
    year_df = pd.DataFrame(year_rows).set_index("Year")
    st.dataframe(year_df, width="stretch")
else:
    st.info("No year-wise data available.")

st.markdown("---")
st.subheader("📊 Parameter Summary")
render_table(stats)
