import streamlit as st
from utils.common import load_database

st.set_page_config(layout="wide")

# Load data
df_database = load_database()

pages = [
    st.Page("pages/fraud_detection.py", title="Automatic Fraud Detection")
]

pg = st.navigation(pages)
pg.run()