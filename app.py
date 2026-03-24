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
# 🌍 WORLD MAP
# =========================
st.subheader("🌍 Global Water Quality Map")

if "Country" in df.columns:
    fig_map = px.scatter_geo(
        df,
        locations="Country",
        locationmode="country names",
        color="CCME_WQI",
        hover_name="Area",
        title="Water Quality by Country"
    )
    st.plotly_chart(fig_map)
else:
    st.warning("Country data not available")

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
# 📂 UPLOAD DATA
# =========================
st.subheader("📂 Upload Your Dataset")

uploaded_file = st.file_uploader("Upload CSV")

if uploaded_file:
    new_df = pd.read_csv(uploaded_file)
    st.write(new_df.head())

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