import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# --- CONFIGURATION ---
FILENAME = "test_data_v2.xlsx"  # NEW FILENAME to avoid cache issues
NUM_PLAYERS = 30
POSITIONS = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
DOMINANCE = ['Right', 'Left']

def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

print(f"Generating data for {FILENAME}...")

# 1. Create Base Data
data_rows = []
for i in range(1, NUM_PLAYERS + 1):
    pos = random.choice(POSITIONS)
    dom = random.choice(DOMINANCE)
    # 1-3 injuries per player
    num_injuries = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
    
    for j in range(num_injuries):
        injury_date = random_date(datetime(2022, 1, 1), datetime(2024, 7, 1))
        rtt = int(np.random.gamma(shape=2.5, scale=10)) 
        if rtt < 5: rtt = 5 
        rtp = rtt + int(np.random.gamma(shape=2, scale=5))
        
        data_rows.append({
            "Unique_ID": f"P{i}_I{j+1}",
            "Position": pos,
            "Dominant": dom,
            "Date_NA": injury_date.strftime("%d/%m/%Y"),
            "RTT_Days": rtt,
            "RTP_Days": rtp,
        })

df_base = pd.DataFrame(data_rows)

# 2. Reshape to "Messy" Audit Format
# These match the app's expectations exactly
metrics = [
    ("Injury_Characteristic", "Position"),
    ("Injury_Characteristic", "Dominant / non-dominant"),
    ("Date", "NA"), 
    ("RTP_Day", "RTT (full, unrestricted)"),
    ("RTP_Day", "RTP (start or sub, competitive game)")
]

excel_data = {
    "Rehab audit details": [],
    "...2": [],
    "...3": [] 
}

# Create columns for every injury
for col in df_base["Unique_ID"]:
    excel_data[col] = []

for cat, sub_cat in metrics:
    excel_data["Rehab audit details"].append(cat)
    excel_data["...2"].append(sub_cat)
    excel_data["...3"].append("valid_row") # Dummy text to prevent filtering issues
    
    for _, row in df_base.iterrows():
        val = None
        if sub_cat == "Position": val = row["Position"]
        elif sub_cat == "Dominant / non-dominant": val = row["Dominant"]
        elif sub_cat == "NA": val = row["Date_NA"]
        elif "RTT" in sub_cat: val = row["RTT_Days"]
        elif "RTP" in sub_cat: val = row["RTP_Days"]
        excel_data[row["Unique_ID"]].append(val)

# 3. Export
df_export = pd.DataFrame(excel_data)
df_export.to_excel(FILENAME, index=False)
print(f"SUCCESS: Created '{FILENAME}' with {len(df_base)} injuries.")