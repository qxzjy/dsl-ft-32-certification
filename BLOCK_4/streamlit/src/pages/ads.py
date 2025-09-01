import streamlit as st
from utils.common import load_data

# Load data
data = load_data()

st.title("Est'Immo 🏠")

st.markdown("# 📊 Nos estimations de biens")

st.divider()

st.write(data)
