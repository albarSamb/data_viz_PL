"""
Fonctions partagées par toutes les pages du dashboard.

- chargement des 5 saisons (mis en cache avec @st.cache_data)
- passage du format "1 ligne = 1 match" au format "1 ligne = 1 équipe x 1 match"
- calcul des 3 KPI
- filtres de la sidebar (identiques sur chaque page)
"""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

# Fichiers bruts football-data.co.uk (division E0 = Premier League)
SAISONS = {
    "2019-20": "E0_1920.csv",
    "2020-21": "E0_2021.csv",
    "2021-22": "E0_2122.csv",
    "2022-23": "E0_2223.csv",
    "2023-24": "E0_2324.csv",
}

COLONNES = [
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HS", "AS", "HST", "AST", "HF", "AF", "HY", "AY", "HR", "AR",
]

# Pondération de l'indice disciplinaire : un jaune vaut 1, un rouge vaut 3
# (3 = suspension standard FA pour conduite violente, cf. page Méthode).
POIDS_JAUNE = 1
POIDS_ROUGE = 3

TOUTES = "Toutes les équipes"

# Couleurs du dashboard (palette validée daltonisme : bleu, orange, gris)
COULEUR_EQUIPE = "#2a78d6"
COULEUR_LIGUE = "#eb6834"
COULEUR_AUTRES = "#c3c2b7"
COULEUR_MOYENNE = "#898781"
# Ordre fixe des couleurs : équipe filtrée puis équipes de comparaison (max 3)
PALETTE_EQUIPES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
MAX_COMPARAISON = 3


@st.cache_data
def charger_matchs() -> pd.DataFrame:
    """Lit les 5 CSV et renvoie un DataFrame : 1 ligne = 1 match (1900 lignes)."""
    morceaux = []
    for saison, fichier in SAISONS.items():
        df_s = pd.read_csv(DATA_DIR / fichier, usecols=COLONNES)
        df_s["Saison"] = saison
        morceaux.append(df_s)
    df = pd.concat(morceaux, ignore_index=True)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    return df


@st.cache_data
def matchs_par_equipe() -> pd.DataFrame:
    """
    Renvoie 1 ligne = 1 équipe x 1 match (3800 lignes).
    Chaque match apparaît deux fois : une fois vu du domicile, une fois vu de l'extérieur.
    """
    df = charger_matchs()

    dom = pd.DataFrame({
        "Saison": df["Saison"], "Date": df["Date"],
        "Equipe": df["HomeTeam"], "Adversaire": df["AwayTeam"], "Lieu": "Domicile",
        "Buts": df["FTHG"], "Buts_encaisses": df["FTAG"],
        "Tirs": df["HS"], "Tirs_cadres": df["HST"],
        "Fautes": df["HF"], "Jaunes": df["HY"], "Rouges": df["HR"],
        "Points": df["FTR"].map({"H": 3, "D": 1, "A": 0}),
    })
    ext = pd.DataFrame({
        "Saison": df["Saison"], "Date": df["Date"],
        "Equipe": df["AwayTeam"], "Adversaire": df["HomeTeam"], "Lieu": "Extérieur",
        "Buts": df["FTAG"], "Buts_encaisses": df["FTHG"],
        "Tirs": df["AS"], "Tirs_cadres": df["AST"],
        "Fautes": df["AF"], "Jaunes": df["AY"], "Rouges": df["AR"],
        "Points": df["FTR"].map({"A": 3, "D": 1, "H": 0}),
    })
    return pd.concat([dom, ext], ignore_index=True)


def calculer_kpis(df: pd.DataFrame, par: list[str]) -> pd.DataFrame:
    """
    Agrège les matchs selon les colonnes `par` et calcule les 3 KPI.

    - Taux de cadrage    = tirs cadrés / tirs
    - Taux de conversion = buts / tirs cadrés
    - Indice discipline  = (jaunes + 3 x rouges) / matchs

    Les ratios sont calculés sur les sommes (et non en moyenne des ratios par match)
    pour éviter les divisions par zéro et le bruit des matchs à 0 tir cadré.
    """
    agg = df.groupby(par).agg(
        Matchs=("Buts", "size"),
        Buts=("Buts", "sum"),
        Tirs=("Tirs", "sum"),
        Tirs_cadres=("Tirs_cadres", "sum"),
        Jaunes=("Jaunes", "sum"),
        Rouges=("Rouges", "sum"),
        Points=("Points", "sum"),
    ).reset_index()

    agg["Taux de cadrage"] = agg["Tirs_cadres"] / agg["Tirs"]
    agg["Taux de conversion"] = agg["Buts"] / agg["Tirs_cadres"]
    agg["Indice discipline"] = (POIDS_JAUNE * agg["Jaunes"] + POIDS_ROUGE * agg["Rouges"]) / agg["Matchs"]
    agg["Points par match"] = agg["Points"] / agg["Matchs"]
    return agg


@st.cache_data
def ecarts_top_bas() -> pd.DataFrame:
    """
    Compare, sur les 5 saisons et tous matchs confondus, le top 6 de chaque saison
    aux 3 relégués (les 3 derniers du classement). Sert au message clé du dashboard.
    """
    ts = calculer_kpis(matchs_par_equipe(), ["Saison", "Equipe"])
    ts = ts.sort_values(["Saison", "Points", "Buts"], ascending=[True, False, False])
    top = ts.groupby("Saison").head(6).assign(Groupe="Top 6")
    bas = ts.groupby("Saison").tail(3).assign(Groupe="Relégués")
    groupes = pd.concat([top, bas])
    return groupes.groupby("Groupe")[["Taux de cadrage", "Taux de conversion", "Indice discipline"]].mean()


def _choix_persistant(widget, label: str, options: list, cle: str, defaut, **kwargs):
    """
    Widget dont la valeur survit au changement de page.
    Streamlit efface l'état d'un widget quand on change de page ; on garde donc
    la valeur choisie dans une clé séparée de session_state et on la redonne au widget.
    """
    valeur = st.session_state.get(cle, defaut)
    if valeur not in options:
        valeur = defaut
    choix = widget(label, options, index=options.index(valeur), key=f"{cle}_widget", **kwargs)
    st.session_state[cle] = choix
    return choix


def filtres_sidebar(df: pd.DataFrame) -> tuple[str, str, str, list[str]]:
    """
    Affiche les filtres dans la sidebar et renvoie (saison, equipe, lieu, comparaison).
    `comparaison` est la liste (0 à 3) des équipes à comparer à l'équipe filtrée.
    Les choix sont conservés d'une page à l'autre (voir _choix_persistant).
    """
    st.sidebar.header("Filtres")

    saisons = list(SAISONS.keys())
    saison = _choix_persistant(st.sidebar.selectbox, "Saison", saisons, "saison", saisons[-1])

    equipes = [TOUTES] + sorted(df.loc[df["Saison"] == saison, "Equipe"].unique())
    equipe = _choix_persistant(st.sidebar.selectbox, "Équipe", equipes, "equipe", TOUTES)

    lieu = _choix_persistant(st.sidebar.radio, "Lieu", ["Tous", "Domicile", "Extérieur"], "lieu", "Tous", horizontal=True)

    # Équipes de comparaison : toutes les équipes vues sur les 5 saisons, sauf l'équipe filtrée
    candidates = [e for e in sorted(df["Equipe"].unique()) if e != equipe]
    memo = [e for e in st.session_state.get("comparaison", []) if e in candidates]
    comparaison = st.sidebar.multiselect(
        "Comparer avec (3 max)", candidates, default=memo, key="comparaison_widget",
        max_selections=MAX_COMPARAISON,
        help="Ajoute ces équipes aux courbes sur 5 saisons, au comparatif de la saison et au nuage de points.",
    )
    st.session_state["comparaison"] = comparaison

    st.sidebar.caption(
        "Source : football-data.co.uk, Premier League 2019-20 à 2023-24, "
        "1 900 matchs."
    )
    return saison, equipe, lieu, comparaison


def appliquer_lieu(df: pd.DataFrame, lieu: str) -> pd.DataFrame:
    """Filtre domicile / extérieur ('Tous' ne filtre rien)."""
    if lieu == "Tous":
        return df
    return df[df["Lieu"] == lieu]


def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f} %"


def fmt_pts(x: float, decimales: int = 1) -> str:
    return f"{x:+.{decimales}f} pt"
