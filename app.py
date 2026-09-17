"""
Point d'entrée du dashboard : déclare les pages et lance la navigation.
Lancer avec :  streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Premier League : les trois écarts du classement",
    page_icon="⚽",
    layout="wide",
)

pages = [
    st.Page("pages/1_Synthese.py", title="Synthèse", default=True),
    st.Page("pages/2_Detail_equipe.py", title="Détail équipe"),
    st.Page("pages/3_Methode.py", title="Méthode et données"),
]

st.navigation(pages).run()
