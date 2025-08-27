import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.common import load_database, display_detailed_stats

df_database = load_database()

st.markdown("# Détection de paiements frauduleux")

st.markdown("## Statistiques gobales")

col1, col2 = st.columns(2)

with col1:

    data = df_database.groupby("is_fraud").size().reset_index(name="count")
    data["is_fraud"] = data["is_fraud"].map({0: "Paiements licites", 1: "Paiments frauduleux"})
    
    fig_1 = px.pie(
        data_frame=data,
        names="is_fraud",
        values="count",
        title="Répartition des paiements"
    )

    st.plotly_chart(fig_1, use_container_width=True)

with col2:

    data = df_database[df_database["is_fraud"]==1].groupby("category").size().reset_index(name="count")
    data["category"] = data["category"].map({
        "gas_transport": "Transport de gaz",
        "grocery_pos": "Épicerie",
        "home": "Mobilier / Décoration",
        "shopping_pos": "Magasin",
        "kids_pets": "Animaux de compagnies",
        "shopping_net": "Magasin en ligne",
        "entertainment": "Divertissement",
        "personal_care": "Soins personnels",
        "food_dining": "Restauration",
        "health_fitness": "Santé et remise en forme",
        "misc_pos": "Divers",
        "misc_net": "Divers en ligne",
        "grocery_net": "Épicerie en ligne",
        "travel": "Voyage"
    })
    
    fig_2 = px.bar(
        data_frame=data,
        x="category",
        y="count",
        title="Répartition des fraudes par type d'enseigne"
    )

    st.plotly_chart(fig_2, use_container_width=True)

st.markdown("## Statistiques détaillées")

tab1, tab2 = st.tabs(["Aujourd'hui", "Hier"])

with tab1:

    display_detailed_stats(datetime.today().strftime("%Y-%m-%d"))
            
with tab2:

    yesterday = datetime.today() - timedelta(days=1)

    display_detailed_stats(yesterday.strftime("%Y-%m-%d"))