import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ---------------- CONFIG ----------------
DATA_FILE = "comments.csv"
ANNOTATION_FILE = "annotations.csv"

LABELS = [
    "non-hate",
    "political hate",
    "religious hate",
    "gender-based hate",
    "threat",
    "abusive",
    "other"
]

# ---------------- LOAD DATA ----------------
df = pd.read_csv(DATA_FILE)

# ---------------- USER LOGIN ----------------
st.title("📝 Comment Annotation Tool")

if "annotator" not in st.session_state:
    st.session_state.annotator = ""

st.session_state.annotator = st.text_input(
    "Enter your Annotator ID (e.g., your name)",
    st.session_state.annotator
)

if not st.session_state.annotator:
    st.stop()

# ---------------- SESSION STATE ----------------
if "index" not in st.session_state:
    st.session_state.index = 0

# ---------------- CURRENT ROW ----------------
if st.session_state.index >= len(df):
    st.success("🎉 All comments annotated. Thank you!")
    st.stop()

row = df.iloc[st.session_state.index]

# ---------------- DISPLAY COMMENT ----------------
st.markdown("### 📌 Comment Information")

st.write(f"**Timestamp:** {row['Timestamp']}")
st.write(f"**Username:** {row['Username']}")
st.write(f"**Video ID:** {row['VideoID']}")
st.write(f"**Date:** {row['Date']}")

st.markdown("### 💬 Comment Text")
st.info(row["Comment"])

# ---------------- LABEL SELECTION ----------------
label = st.radio(
    "Select annotation label:",
    LABELS,
    horizontal=False
)

# ---------------- SAVE FUNCTION ----------------
def save_annotation():
    record = {
        "Timestamp": row["Timestamp"],
        "Username": row["Username"],
        "VideoID": row["VideoID"],
        "Comment": row["Comment"],
        "Date": row["Date"],
        "annotator": st.session_state.annotator,
        "label": label,
        "annotated_at": datetime.now()
    }

    out_df = pd.DataFrame([record])

    if os.path.exists(ANNOTATION_FILE):
        out_df.to_csv(ANNOTATION_FILE, mode="a", header=False, index=False)
    else:
        out_df.to_csv(ANNOTATION_FILE, index=False)

# ---------------- SUBMIT ----------------
if st.button("✅ Submit & Next"):
    save_annotation()
    st.session_state.index += 1
    st.rerun()

# ---------------- PROGRESS ----------------
st.progress((st.session_state.index + 1) / len(df))
st.caption(f"Annotated {st.session_state.index + 1} / {len(df)}")
