import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from openai import OpenAI

# =========================================
# 🔑 OPENAI SETUP
# =========================================
client = OpenAI(api_key="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")  # 🔥 replace this

# =========================================
# 🎯 PAGE CONFIG
# =========================================
st.set_page_config(page_title="AI Financial Analyzer", layout="wide")

# =========================================
# 🎯 SIDEBAR
# =========================================
st.sidebar.title("🔍 Controls")

option = st.sidebar.selectbox(
    "Select Section",
    ["Overview", "Anomaly Detection", "Workpaper"]
)

st.title("📊 AI Financial Statement Analyzer")

# =========================================
# 📂 FILE UPLOAD
# =========================================
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # Convert Date
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort data
    df = df.sort_values(by='Date')

    # =========================================
    # 📈 FEATURE ENGINEERING
    # =========================================
    df['Earnings_Growth'] = df['Earnings'].pct_change()
    df['Price_Change'] = df['SP500'].pct_change()

    df['z_score'] = (df['Earnings'] - df['Earnings'].mean()) / df['Earnings'].std()
    df['Anomaly'] = df['z_score'].abs() > 2

    anomalies = df[df['Anomaly']]

    # =========================================
    # 📊 OVERVIEW
    # =========================================
    if option == "Overview":

        st.subheader("📄 Dataset Preview")
        st.dataframe(df.head())

        col1, col2, col3 = st.columns(3)

        col1.metric("📈 Avg Earnings", round(df['Earnings'].mean(), 2))
        col2.metric("⚠️ Anomalies", int(df['Anomaly'].sum()))
        col3.metric("📊 Max SP500", round(df['SP500'].max(), 2))

    # =========================================
    # ⚠️ ANOMALY DETECTION
    # =========================================
    elif option == "Anomaly Detection":

        st.subheader("📈 Earnings Trend with Anomalies")

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df['Date'], df['Earnings'], label='Earnings')

        ax.scatter(anomalies['Date'], anomalies['Earnings'], label='Anomalies')

        ax.legend()
        st.pyplot(fig)

        # Risk Level
        st.subheader("🚨 Risk Level")

        risk_count = df['Anomaly'].sum()

        if risk_count > 10:
            st.error("🔴 High Risk Detected")
        elif risk_count > 5:
            st.warning("🟡 Medium Risk")
        else:
            st.success("🟢 Low Risk")

        # Show anomalies
        st.subheader("⚠️ Detected Anomalies")
        st.dataframe(anomalies[['Date', 'Earnings', 'z_score']])

        # =========================================
        # 🤖 AI INSIGHT (OPENAI)
        # =========================================
        st.subheader("🤖 AI Insight")

        if len(anomalies) > 0:
            selected = anomalies.iloc[0]

            prompt = f"""
            You are an audit assistant.

            Analyze this financial anomaly:
            Date: {selected['Date']}
            Earnings: {selected['Earnings']}
            Z-score: {selected['z_score']}

            Explain:
            - Why this is risky
            - What auditor should check
            - Keep it concise and professional
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )

                st.success(response.choices[0].message.content)

            except Exception as e:
                st.error(f"AI Error: {e}")

    # =========================================
    # 📄 WORKPAPER GENERATOR
    # =========================================
    elif option == "Workpaper":

        st.subheader("📊 Audit Summary")

        total_earnings = df['Earnings'].sum()
        total_sp500 = df['SP500'].sum()

        st.write(f"Total Earnings: {round(total_earnings,2)}")
        st.write(f"Total SP500: {round(total_sp500,2)}")

        # Audit Commentary
        st.subheader("🧠 Audit Commentary")

        if len(df) > 1:
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            growth = ((latest['Earnings'] - prev['Earnings']) / prev['Earnings']) * 100

            if growth > 20:
                comment = f"Earnings increased by {round(growth,2)}%, which is unusually high and requires audit attention."
            elif growth < -20:
                comment = f"Earnings decreased by {round(abs(growth),2)}%, indicating potential risk or business decline."
            else:
                comment = f"Earnings change of {round(growth,2)}% appears reasonable."

            st.info(comment)

        # =========================================
        # 📥 EXCEL WORKPAPER DOWNLOAD
        # =========================================
        st.subheader("📥 Download Professional Workpaper")

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:

            df.to_excel(writer, sheet_name='Full Data', index=False)
            anomalies.to_excel(writer, sheet_name='Anomalies', index=False)

            summary_df = pd.DataFrame({
                "Metric": ["Total Earnings", "Total SP500", "Anomaly Count"],
                "Value": [
                    round(total_earnings, 2),
                    round(total_sp500, 2),
                    int(df['Anomaly'].sum())
                ]
            })

            summary_df.to_excel(writer, sheet_name='Audit Summary', index=False)

        st.download_button(
            label="📄 Download Excel Workpaper",
            data=output.getvalue(),
            file_name="audit_workpaper.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.info("👆 Upload a CSV file to begin")