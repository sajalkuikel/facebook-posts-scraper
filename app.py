import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ---------------- CONFIG ----------------
DATA_URL = "https://raw.githubusercontent.com/sajalkuikel/facebook-posts-scraper/refs/heads/main/comments.csv"
DB_FILE = "annotations.db"

LABELS = [
    "non-hate",
    "political hate",
    "religious hate",
    "gender-based hate",
    "threat",
    "abusive",
    "other"
]

# ---------------- DB INIT ----------------
@st.cache_resource
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS annotations (
            row_id INTEGER,
            annotator TEXT,
            label TEXT,
            annotated_at TEXT,
            PRIMARY KEY (row_id, annotator)
        )
    """)
    return conn

conn = get_db()

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    df["row_id"] = df.index
    return df

data = load_data()

# ---------------- UI ----------------
st.title("📝 Comment Annotation Tool")

annotator = st.text_input("Enter Annotator ID")

if not annotator:
    st.stop()

# ---------------- FETCH PROGRESS ----------------
done_ids = pd.read_sql(
    "SELECT row_id FROM annotations WHERE annotator = ?",
    conn,
    params=(annotator,)
)["row_id"].tolist()

remaining = data[~data["row_id"].isin(done_ids)]

# ---------------- DONE ----------------
if remaining.empty:
    st.success("🎉 You have completed all annotations. Thank you!")
    st.stop()

row = remaining.iloc[0]

# ---------------- DISPLAY ----------------
st.markdown("### 💬 Comment")
st.info(row["Comment"])

st.write(f"**Username:** {row['Username']}")
st.write(f"**Video ID:** {row['VideoID']}")
st.write(f"**Timestamp:** {row['Timestamp']}")
st.write(f"**Date:** {row['Date']}")

# ---------------- LABEL ----------------
label = st.radio("Select label", LABELS)

# ---------------- SUBMIT ----------------
if st.button("✅ Submit & Next"):
    conn.execute(
        "INSERT OR REPLACE INTO annotations VALUES (?, ?, ?, ?)",
        (
            int(row["row_id"]),
            annotator,
            label,
            datetime.now().isoformat()
        )
    )
    conn.commit()
    st.rerun()

# ---------------- PROGRESS ----------------
progress = len(done_ids) / len(data)
st.progress(progress)
st.caption(f"Annotated {len(done_ids)} / {len(data)}")
