# Dashboard Premier League 

Dashboard Streamlit construit à partir du projet d'Analyse Exploratoire de Données (Premier League 2019-20 à 2023-24).

## Contenu du dossier

```
dashboard_premier_league/
├── app.py                   # point d'entrée : déclare les 3 pages (st.navigation)
├── pages/
│   ├── 1_Synthese.py        # message, KPI, 2 visualisations en onglets
│   ├── 2_Detail_equipe.py   # trajectoire 5 saisons, comparaison entre équipes, domicile/extérieur, classement
│   └── 3_Methode.py         # définitions, hypothèses, limites
├── utils.py                 # chargement (cache), calcul des KPI, filtres sidebar
├── data/E0_*.csv            # 5 fichiers bruts football-data.co.uk
├── cadrage.md               # document de cadrage (message, audience, KPI, structure)
├── requirements.txt
└── .streamlit/config.toml   # thème
```

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Le dashboard s'ouvre sur http://localhost:8501.

Ouvrir d'abord l'URL racine (pas un lien direct vers une sous-page) : c'est `app.py` qui déclare les pages avec `st.navigation`. Si la toute première requête après un démarrage vise une sous-page, Streamlit bascule sur son ancien mode multipage (noms de pages bruts dans la sidebar). Un passage par la racine suffit à rétablir la navigation normale.

Les CSV sont dans le dépôt, il n'y a donc aucune dépendance réseau au moment du déploiement.
