import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import time

# =========================
# LOAD MODEL + DATA
# =========================
model = pickle.load(open("model.pkl", "rb"))
le = pickle.load(open("encoder.pkl", "rb"))
features = pickle.load(open("features.pkl", "rb"))

df = pd.read_csv("data.csv")
df.columns = df.columns.str.strip()

st.set_page_config(layout="wide")

st.title("🌊 Coastal Water Quality Monitoring System")

# =========================
# WORLD MAP WITH HIGHLIGHT
# =========================
st.subheader("🌍 Global Water Quality Map")

# Aggregate your data
map_df = df.groupby("Country")["CCME_Values"].mean().reset_index()

# Base map (all countries in grey)
fig_map = px.choropleth(
    locations=[],
)


fig_map = px.choropleth(
    map_df,
    locations="Country",
    locationmode="country names",
    color="CCME_Values",
    color_continuous_scale="RdYlGn",
)


fig_map.update_geos(
    showland=True,
    landcolor="lightgrey",   # all countries visible
    showcountries=True,
    countrycolor="white",
    showframe=False,
    showcoastlines=False,
    projection_type="natural earth",
    bgcolor="#0e1117"
)

# Layout fixes
fig_map.update_layout(
    dragmode=False,
    height=500,
    margin={"r":0,"t":0,"l":0,"b":0},
    paper_bgcolor="#0e1117",
    font=dict(color="white"),
)

st.plotly_chart(fig_map, use_container_width=True)
# =========================
# 📊 VISUALIZATIONS
# =========================
col1, col2 = st.columns(2)

with col1:
    fig1 = px.histogram(df, x="CCME_WQI", title="Water Quality Distribution")
    st.plotly_chart(fig1)

with col2:
    fig2 = px.scatter(
        df,
        x="Nitrate (mg/l)",
        y="Nitrogen (mg/l)",
        color="CCME_WQI",
        title="Pollution Correlation"
    )
    st.plotly_chart(fig2)

# =========================
# 🔥 REAL-TIME SIMULATION
# =========================
st.subheader("🔄 Real-Time Simulation")

if st.checkbox("Start Simulation"):
    placeholder = st.empty()

    for i in range(10):
        temp_df = df.sample(50)

        fig = px.scatter(
            temp_df,
            x="Nitrate (mg/l)",
            y="Nitrogen (mg/l)",
            color="CCME_WQI",
            title="Live Data Simulation"
        )

        placeholder.plotly_chart(fig)
        time.sleep(1)

# =========================
# 💬 CHAT SEARCH
# =========================
st.subheader("💬 Search Coastal Area")

user_input = st.text_input("Enter Country or Area")

if user_input:
    filtered = df[
        df["Country"].str.contains(user_input, case=False, na=False) |
        df["Area"].str.contains(user_input, case=False, na=False)
    ]

    if not filtered.empty:
        st.success(f"Results for: {user_input}")

        st.write(filtered.head())

        fig = px.histogram(filtered, x="CCME_WQI",
                           title=f"Water Quality in {user_input}")
        st.plotly_chart(fig)

        most_common = filtered["CCME_WQI"].mode()[0]
        st.info(f"Most common quality: {most_common}")

        if most_common in ["Poor", "Marginal"]:
            st.warning("⚠️ High pollution detected")
        else:
            st.success("✅ Water quality acceptable")

    else:
        st.error("No data found")

# =========================
# 🔮 PREDICTION
# =========================
st.subheader("🔮 Predict Water Quality")

input_values = []

for feature in features:
    val = st.number_input(f"{feature}", value=1.0)
    input_values.append(val)

input_df = pd.DataFrame([input_values], columns=features)

if st.button("Predict"):
    pred = model.predict(input_df)
    result = le.inverse_transform(pred)

    proba = model.predict_proba(input_df)
    confidence = np.max(proba)

    st.success(f"Prediction: {result[0]}")
    st.write(f"Confidence: {confidence:.2f}")

# =========================
# 📊 FEATURE IMPORTANCE
# =========================
st.subheader("📊 Feature Importance")

try:
    importances = model.named_steps['model'].estimators_[0].feature_importances_

    fig = px.bar(
        x=features,
        y=importances,
        title="Feature Importance"
    )
    st.plotly_chart(fig)
except:
    st.warning("Feature importance not available")

# =========================
# 📈 TIME TREND
# =========================
if "Date" in df.columns:
    st.subheader("📈 Time Trend")

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values("Date")

    fig3 = px.line(
        df,
        x="Date",
        y="Nitrate (mg/l)",
        title="Nitrate Trend Over Time"
    )
    st.plotly_chart(fig3)

# =========================
# 📂 SMART UPLOAD SYSTEM
# =========================
st.subheader("📂 Upload Dataset for Analysis")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    new_df = pd.read_csv(uploaded_file)
    new_df.columns = new_df.columns.str.strip()

    st.success("Dataset uploaded successfully!")

    # =========================
    # 🔄 STANDARDIZE DATA
    # =========================
    new_df = new_df.rename(columns={
        "country": "Country",
        "temp": "Temperature (cel)",
        "temperature": "Temperature (cel)",
        "ph": "pH (ph units)",
        "oxygen": "Dissolved Oxygen (mg/l)",
        "bod": "Biochemical Oxygen Demand (mg/l)",
        "ammonia": "Ammonia (mg/l)",
        "nitrate": "Nitrate (mg/l)",
        "nitrogen": "Nitrogen (mg/l)",
        "phosphate": "Orthophosphate (mg/l)"
    })

    # Add missing columns if needed
    required_cols = [
        'Ammonia (mg/l)',
        'Biochemical Oxygen Demand (mg/l)',
        'Dissolved Oxygen (mg/l)',
        'Orthophosphate (mg/l)',
        'pH (ph units)',
        'Temperature (cel)',
        'Nitrogen (mg/l)',
        'Nitrate (mg/l)'
    ]

    for col in required_cols:
        if col not in new_df.columns:
            new_df[col] = new_df.select_dtypes(include=np.number).mean(axis=1)

    # =========================
    # 📊 CREATE WQI IF NOT PRESENT
    # =========================
    if "CCME_Values" not in new_df.columns:
        new_df['CCME_Values'] = (
            100
            - (new_df['Biochemical Oxygen Demand (mg/l)'] * 2)
            - (new_df['Ammonia (mg/l)'] * 3)
            - (new_df['Nitrate (mg/l)'] * 2)
        ).clip(0, 100)

    if "CCME_WQI" not in new_df.columns:
        def classify_wqi(val):
            if val >= 95:
                return "Excellent"
            elif val >= 80:
                return "Good"
            elif val >= 65:
                return "Fair"
            elif val >= 45:
                return "Marginal"
            else:
                return "Poor"

        new_df['CCME_WQI'] = new_df['CCME_Values'].apply(classify_wqi)

    # =========================
    # 📊 SHOW DATA
    # =========================
    st.write("Preview:")
    st.dataframe(new_df.head())

    # =========================
    # 📊 VISUALIZATIONS
    # =========================
    st.subheader("📊 Visualizations")

    fig1 = px.histogram(new_df, x="CCME_WQI", title="Water Quality Distribution")
    st.plotly_chart(fig1)

    fig2 = px.scatter(
        new_df,
        x="Nitrate (mg/l)",
        y="Nitrogen (mg/l)",
        color="CCME_WQI",
        title="Pollution Correlation"
    )
    st.plotly_chart(fig2)

    # =========================
    # 🌍 MAP (FULL WORLD)
    # =========================
    if "Country" in new_df.columns:
        map_df = new_df.groupby("Country")["CCME_Values"].mean().reset_index()

        fig_map = px.choropleth(
            map_df,
            locations="Country",
            locationmode="country names",
            color="CCME_Values",
            color_continuous_scale="RdYlGn"
        )

        fig_map.update_geos(
            showland=True,
            landcolor="lightgrey",
            showcountries=True,
            countrycolor="white",
            projection_type="natural earth"
        )

        st.plotly_chart(fig_map, use_container_width=True)

    # =========================
    # 🔮 MODEL PREDICTION
    # =========================
    if all(f in new_df.columns for f in features):
        sample = new_df[features].iloc[0:1]
        pred = model.predict(sample)
        result = le.inverse_transform(pred)

        st.success(f"Prediction for uploaded data: {result[0]}")

# =========================
# 🤖 SIMPLE CHATBOT
# =========================
st.subheader("🤖 AI Assistant")

query = st.text_input("Ask about water quality")

if query:
    if "pollution" in query.lower():
        st.write("High nitrate or nitrogen indicates pollution from agriculture.")
    elif "safe" in query.lower():
        st.write("Excellent or Good WQI indicates safe water.")
    elif "improve" in query.lower():
        st.write("Reduce industrial discharge and improve wastewater treatment.")
    else:
        st.write("Try asking about pollution, safety, or improvement.")
