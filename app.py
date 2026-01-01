import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
DATA_URL = "https://raw.githubusercontent.com/sajalkuikel/facebook-posts-scraper/refs/heads/main/comments.csv"
SHEET_NAME = "annotation_db"

LABELS = [
    "non-hate",
    "political hate",
    "religious hate",
    "gender-based hate",
    "threat",
    "abusive",
    "other"
]

# ---------------- GOOGLE SHEETS INIT ----------------
@st.cache_resource
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    gc = gspread.authorize(creds)
    sheet = gc.open(SHEET_NAME).sheet1
    return sheet

sheet = get_sheet()

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    df["row_id"] = df.index
    return df

data = load_data()

# ---------------- UI ----------------
st.title("📝 Multi-User Annotation Tool")

annotator = st.text_input("Enter your Annotator ID")

if not annotator:
    st.stop()

# ---------------- LOAD ANNOTATIONS ----------------
records = sheet.get_all_records()
ann_df = pd.DataFrame(records)

if ann_df.empty:
    ann_df = pd.DataFrame(columns=["row_id", "annotator", "label", "timestamp"])

ann_df["row_id"] = ann_df["row_id"].astype(str)

done_ids = ann_df[
    ann_df["annotator"] == annotator
]["row_id"].tolist()

remaining = data[~data["row_id"].astype(str).isin(done_ids)]

# ---------------- DONE ----------------
if remaining.empty:
    st.success("🎉 You have completed all your annotations!")
    st.stop()

row = remaining.iloc[0]

# ---------------- DISPLAY ----------------
st.markdown("### 💬 Comment")
st.info(row["Comment"])

st.write(f"**Username:** {row['Username']}")
st.write(f"**Video ID:** {row['VideoID']}")
st.write(f"**Date:** {row['Date']}")

# ---------------- LABEL ----------------
label = st.radio("Select label", LABELS)

# ---------------- SUBMIT ----------------
if st.button("✅ Submit & Next"):
    sheet.append_row([
        str(row["row_id"]),
        annotator,
        label,
        datetime.now().isoformat()
    ])
    st.rerun()

# ---------------- PROGRESS ----------------
progress = len(done_ids) / len(data)
st.progress(progress)
st.caption(f"Annotated {len(done_ids)} / {len(data)}")
