import streamlit as st
import pandas as pd
import plotly.express as px
import os
import uuid
from sqlalchemy import create_engine

engine = create_engine(os.getenv("DB_URI"), echo=True)

# DELAY
@st.cache_data
def load_database():

    with engine.connect() as conn :
        database = pd.read_sql('SELECT * FROM fraud_detection', conn, index_col="id")

    return database

def display_detailed_stats(date):

    with engine.connect() as conn :
        data = pd.read_sql(f"SELECT * FROM fraud_detection WHERE CAST(trans_date_trans_time as DATE)  = CAST('{str(date)}' as DATE)", conn, index_col="id")

    col1, col2 = st.columns(2)   

    with col1:

        data_pie = data.groupby("is_fraud").size().reset_index(name="count")
        data_pie["is_fraud"] = data_pie["is_fraud"].map({0: "Paiements licites", 1: "Paiments frauduleux"})
        
        fig = px.pie(
            data_frame=data_pie,
            names="is_fraud",
            values="count",
            title="Répartition des paiements"
        )

        st.plotly_chart(fig, use_container_width=True, key=uuid.uuid4())

    with col2:

        st.markdown(f"#### Paiements licites : {len(data[data["is_fraud"]==0])}")
        st.write(data[data["is_fraud"]==0])

        st.markdown(f"#### Paiements frauduleux : {len(data[data["is_fraud"]==1])} ({round(data[data["is_fraud"]==1]['amt'].sum(),2)} $)")
        st.write(data[data["is_fraud"]==1])