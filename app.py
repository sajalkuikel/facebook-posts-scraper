import pandas as pd

df = pd.read_csv("comments.csv")
df["row_id"] = df.index
df.to_csv("comments.csv", index=False)


import streamlit as st
import pandas as pd
import os
from datetime import datetime

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

st.title("📝 Comment Annotation Tool")

# -------- Load data --------
data = pd.read_csv(DATA_FILE)

# -------- Login --------
annotator = st.text_input("Enter Annotator ID")

if not annotator:
    st.stop()

# -------- Load annotations --------
if os.path.exists(ANNOTATION_FILE):
    ann = pd.read_csv(ANNOTATION_FILE)
else:
    ann = pd.DataFrame(columns=[
        "row_id", "annotator", "label", "timestamp"
    ])

# -------- Filter already annotated --------
done_ids = ann[ann["annotator"] == annotator]["row_id"].tolist()
remaining = data[~data["row_id"].isin(done_ids)]

# -------- Completion check --------
if remaining.empty:
    st.success("🎉 You have completed all assigned annotations!")
    st.stop()

# -------- Pick next row --------
row = remaining.iloc[0]

# -------- Display --------
st.markdown("### 💬 Comment")
st.info(row["Comment"])

st.write(f"**Video ID:** {row['VideoID']}")
st.write(f"**Username:** {row['Username']}")
st.write(f"**Date:** {row['Date']}")

# -------- Label --------
label = st.radio("Select label", LABELS)

# -------- Save --------
if st.button("✅ Submit"):
    new_row = pd.DataFrame([{
        "row_id": row["row_id"],
        "annotator": annotator,
        "label": label,
        "timestamp": datetime.now()
    }])

    if os.path.exists(ANNOTATION_FILE):
        new_row.to_csv(ANNOTATION_FILE, mode="a", header=False, index=False)
    else:
        new_row.to_csv(ANNOTATION_FILE, index=False)

    st.rerun()

# -------- Progress --------
st.progress(len(done_ids) / len(data))
st.caption(f"Annotated {len(done_ids)} / {len(data)}")
