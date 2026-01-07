import streamlit as st
import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter
import plotly.graph_objects as go

# --- CONFIGURATION ---
FILE_PATH = "test_data_v2.xlsx" 

def load_data():
    try:
        # keep_default_na=False stops pandas from turning "NA" text into NaN
        df = pd.read_excel(FILE_PATH)
    except FileNotFoundError:
        st.error(f"❌ File not found: '{FILE_PATH}'.\n\nPlease run: python create_data.py")
        return pd.DataFrame()

    # 1. Rename first column
    df = df.rename(columns={"Rehab audit details": "variable"})

    # 2. Fill missing category labels (Forward Fill)
    df["variable"] = np.where(
        df["...2"] == "Position",
        "Injury_Characteristic",
        df["variable"]
    )
    df["variable"] = df["variable"].ffill()

    # 3. Create the Combined Column Name
    # This creates "Date_NA", "Injury_Characteristic_Position", etc.
    df["variable_name"] = df["variable"].astype(str) + "_" + df["...2"].astype(str)

    # 4. Filter out unwanted rows
    df = df[df["variable"] != "Reflection and Improvement"]

    # 5. Reshape (Melt -> Pivot)
    injury_cols = df.columns[3:]
    long_df = df.melt(
        id_vars=["variable_name"],
        value_vars=injury_cols,
        var_name="Injury Instance",
        value_name="Context"
    )

    wide_df = long_df.pivot(
        index="Injury Instance",
        columns="variable_name",
        values="Context"
    ).reset_index()

    # --- THE FIX: Handle the 'Date_nan' issue ---
    if "Date_nan" in wide_df.columns:
        wide_df = wide_df.rename(columns={"Date_nan": "Date_NA"})

    return wide_df

# --- LOAD DATA ---
df = load_data()

if df.empty:
    st.stop()

# --- DEBUG CHECK ---
if "Date_NA" not in df.columns:
    st.error("⚠️ CRITICAL ERROR: 'Date_NA' column is still missing.")
    st.write("Columns found:", df.columns.tolist())
    st.stop()

# --- DATA CLEANING ---
# Parse Dates
df["injury_date"] = pd.to_datetime(df["Date_NA"], format="%d/%m/%Y", errors="coerce")

# Parse Days (Handle naming variations)
rtt_col = "RTP_Day_RTT (full, unrestricted)"
rtp_col = "RTP_Day_RTP (start or sub, competitive game)"

df["Date_RTT_days"] = pd.to_numeric(df.get(rtt_col, np.nan), errors="coerce")
df["Date_RTP_days"] = pd.to_numeric(df.get(rtp_col, np.nan), errors="coerce")

# Clean Dominance
dom_col = "Injury_Characteristic_Dominant / non-dominant"
if dom_col in df.columns:
    df = df.rename(columns={dom_col: "Injury_Characteristic_Dominant"})

# --- SIDEBAR & PLOTTING ---
st.sidebar.title("Hamstring Rehab App")

outcome_map = {
    "Return to Training (RTT)": "Date_RTT_days",
    "Return to Play (RTP)": "Date_RTP_days"
}

outcome_label = st.sidebar.selectbox("Select Outcome", list(outcome_map.keys()))
curve_col = outcome_map[outcome_label]

# Filter Logic
positions = sorted(df["Injury_Characteristic_Position"].astype(str).unique())
pos_selected = st.sidebar.multiselect("Position", positions, default=positions)

filtered = df[
    df[curve_col].notna() & (df[curve_col] > 0) &
    df["Injury_Characteristic_Position"].isin(pos_selected)
]

st.title(f"Analysis: {outcome_label}")

if filtered.empty:
    st.warning("No data found for these filters.")
    st.stop()

# ... (rest of the code above remains the same)

# Plot
kmf = KaplanMeierFitter()
kmf.fit(filtered[curve_col], label="Recovery Curve")

# ROBUST FIX: Access the first column by position (iloc) so names don't matter
survival_prob = kmf.survival_function_.iloc[:, 0]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=kmf.survival_function_.index,
    y=1 - survival_prob, # Inverted for Recovery Curve (1 - Survival)
    mode="lines",
    name="Recovery Curve",
    line=dict(shape='hv', width=3)
))

fig.update_layout(
    yaxis_tickformat=".0%", 
    title="Cumulative % Returned to Play",
    xaxis_title="Days since injury",
    yaxis_title="% of Players Returned"
)
st.plotly_chart(fig)

st.write("### Data Preview", filtered.head())