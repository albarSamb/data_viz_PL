"""
Page Synthèse : le message, la zone KPI et les deux visualisations clés.
"""

import altair as alt
import pandas as pd
import streamlit as st

from utils import (
    COULEUR_AUTRES, COULEUR_EQUIPE, COULEUR_LIGUE, PALETTE_EQUIPES, SAISONS, TOUTES,
    appliquer_lieu, calculer_kpis, ecarts_top_bas, filtres_sidebar,
    fmt_pct, matchs_par_equipe,
)


# ----------------------------------------------------------------------------
# Données et filtres
# ----------------------------------------------------------------------------
df = matchs_par_equipe()
saison, equipe, lieu, comparaison = filtres_sidebar(df)
d = appliquer_lieu(df, lieu)

kpi_equipes = calculer_kpis(d[d["Saison"] == saison], ["Equipe"])          # 20 lignes
kpi_ligue = calculer_kpis(d, ["Saison"]).set_index("Saison")                # 5 lignes
kpi_equipe_saisons = calculer_kpis(d, ["Saison", "Equipe"])                 # 100 lignes

# ----------------------------------------------------------------------------
# Titre = le message, pas le nom du dataset
# ----------------------------------------------------------------------------
ecarts = ecarts_top_bas()
top, bas = ecarts.loc["Top 6"], ecarts.loc["Relégués"]

st.title("Convertir, cadrer, rester discipliné : les trois écarts qui séparent le top 6 des relégués")
st.markdown(
    f"Sur 5 saisons de Premier League (1 900 matchs), le top 6 convertit "
    f"**{fmt_pct(top['Taux de conversion'])}** de ses tirs cadrés contre "
    f"**{fmt_pct(bas['Taux de conversion'])}** pour les relégués, cadre "
    f"**{fmt_pct(top['Taux de cadrage'])}** de ses tirs contre "
    f"**{fmt_pct(bas['Taux de cadrage'])}**, et prend "
    f"**{top['Indice discipline']:.2f}** carton pondéré par match contre "
    f"**{bas['Indice discipline']:.2f}**. "
    "Ces trois leviers se travaillent à l'entraînement, contrairement au nombre de buts."
)

# ----------------------------------------------------------------------------
# Zone KPI : 3 tuiles, chacune avec une comparaison (delta) et une tendance (mini-courbe)
# ----------------------------------------------------------------------------
KPIS = [
    # (nom, format valeur, format delta, sens : True si "plus haut = mieux")
    ("Taux de cadrage", lambda v: fmt_pct(v), lambda v: f"{v * 100:+.1f} pt", True),
    ("Taux de conversion", lambda v: fmt_pct(v), lambda v: f"{v * 100:+.1f} pt", True),
    ("Indice discipline", lambda v: f"{v:.2f}", lambda v: f"{v:+.2f}", False),
]

saisons = list(SAISONS.keys())
saison_prec = saisons[saisons.index(saison) - 1] if saisons.index(saison) > 0 else None

if equipe == TOUTES:
    st.subheader(f"Toute la ligue, saison {saison}" + (f", {lieu.lower()}" if lieu != "Tous" else ""))
    contexte = f"vs {saison_prec}" if saison_prec else "première saison"
else:
    st.subheader(f"{equipe}, saison {saison}" + (f", {lieu.lower()}" if lieu != "Tous" else ""))
    contexte = "vs moyenne de la ligue"

cols = st.columns(3)
for col, (nom, f_val, f_delta, plus_haut_mieux) in zip(cols, KPIS):
    if equipe == TOUTES:
        valeur = kpi_ligue.loc[saison, nom]
        delta = valeur - kpi_ligue.loc[saison_prec, nom] if saison_prec else None
        tendance = kpi_ligue[nom]
    else:
        valeur = kpi_equipes.set_index("Equipe").loc[equipe, nom]
        delta = valeur - kpi_ligue.loc[saison, nom]
        tendance = (
            kpi_equipe_saisons[kpi_equipe_saisons["Equipe"] == equipe]
            .set_index("Saison")[nom]
            .reindex(saisons)
        )
    with col:
        st.metric(
            label=nom,
            value=f_val(valeur),
            delta=f_delta(delta) if delta is not None else None,
            delta_color="normal" if plus_haut_mieux else "inverse",
            delta_description=contexte,
            chart_data=tendance.dropna(),
            chart_type="line",
            border=True,
            help={
                "Taux de cadrage": "Tirs cadrés / tirs tentés.",
                "Taux de conversion": "Buts / tirs cadrés.",
                "Indice discipline": "(Cartons jaunes + 3 × cartons rouges) / matchs. Plus bas = mieux.",
            }[nom],
        )
st.caption(
    "Delta : écart à la moyenne de la ligue sur la saison filtrée (ou à la saison précédente quand toute la ligue est affichée). "
    "Mini-courbe : évolution sur les 5 saisons. Vert = dans le bon sens, y compris pour la discipline où plus bas est mieux."
)

# ----------------------------------------------------------------------------
# Zone détail : un onglet par visualisation, réactifs aux 3 filtres
# ----------------------------------------------------------------------------
tab_offensif, tab_discipline = st.tabs(["Cadrage × conversion", "Discipline"])

base = kpi_equipes.copy()
base["Sélection"] = base["Equipe"] == equipe

# Couleur par équipe : équipe filtrée puis équipes de comparaison (ordre fixe), les autres en gris
mises_en_avant = ([equipe] if equipe != TOUTES else []) + [c for c in comparaison if c in set(base["Equipe"])]
if mises_en_avant:
    couleurs = dict(zip(mises_en_avant, PALETTE_EQUIPES[:len(mises_en_avant)] if equipe != TOUTES else PALETTE_EQUIPES[1:len(mises_en_avant) + 1]))
    base["Couleur"] = base["Equipe"].map(couleurs).fillna(COULEUR_AUTRES)
else:
    base["Couleur"] = COULEUR_EQUIPE
moy_cadrage = kpi_ligue.loc[saison, "Taux de cadrage"]
moy_conv = kpi_ligue.loc[saison, "Taux de conversion"]
moy_disc = kpi_ligue.loc[saison, "Indice discipline"]

with tab_offensif:
    st.markdown(f"**Où se situe chaque équipe sur les deux leviers offensifs, saison {saison}**")

    # Emphase : équipe filtrée et équipes de comparaison en couleur, les autres en gris.
    couleur = alt.Color("Couleur:N", scale=None)

    points = (
        alt.Chart(base)
        .mark_circle(opacity=0.85, stroke="white", strokeWidth=1.5)
        .encode(
            x=alt.X("Taux de cadrage:Q", axis=alt.Axis(format=".0%", title="Taux de cadrage (tirs cadrés / tirs)"),
                    scale=alt.Scale(zero=False, padding=20)),
            y=alt.Y("Taux de conversion:Q", axis=alt.Axis(format=".0%", title="Taux de conversion (buts / tirs cadrés)"),
                    scale=alt.Scale(zero=False, padding=36)),
            size=alt.Size("Points:Q", scale=alt.Scale(range=[80, 900]), legend=alt.Legend(title="Points", values=[20, 40, 60, 80])),
            color=couleur,
            tooltip=[
                alt.Tooltip("Equipe:N", title="Équipe"),
                alt.Tooltip("Points:Q"),
                alt.Tooltip("Taux de cadrage:Q", format=".1%"),
                alt.Tooltip("Taux de conversion:Q", format=".1%"),
                alt.Tooltip("Tirs:Q"),
                alt.Tooltip("Buts:Q"),
            ],
        )
    )

    # Étiquettes directes sélectives : équipe filtrée, 3 premiers et 3 derniers au classement
    tri = base.sort_values("Points", ascending=False)
    a_etiqueter = set(tri.head(3)["Equipe"]) | set(tri.tail(3)["Equipe"]) | set(mises_en_avant)
    etiquettes = (
        alt.Chart(base[base["Equipe"].isin(a_etiqueter)])
        .mark_text(dy=-16, fontSize=12, fontWeight="bold", color="#0b0b0b", clip=False)
        .encode(x="Taux de cadrage:Q", y="Taux de conversion:Q", text="Equipe:N")
    )

    # Moyennes de la ligue en pointillés : les 4 quadrants se lisent sans effort
    regle_x = alt.Chart(pd.DataFrame({"x": [moy_cadrage]})).mark_rule(strokeDash=[4, 4], color="#898781").encode(x="x:Q")
    regle_y = alt.Chart(pd.DataFrame({"y": [moy_conv]})).mark_rule(strokeDash=[4, 4], color="#898781").encode(y="y:Q")

    st.altair_chart((regle_x + regle_y + points + etiquettes).properties(height=460), width="stretch")
    st.caption(
        "Nuage de points : deux mesures par équipe, la taille du point donne les points au classement. "
        "Les pointillés sont les moyennes de la ligue : en haut à droite, les équipes qui cadrent et convertissent mieux que la ligue."
    )

with tab_discipline:
    st.markdown(f"**Indice disciplinaire par équipe, saison {saison}** (jaune = 1, rouge = 3, par match)")

    couleur_barre = alt.Color("Couleur:N", scale=None)

    barres = (
        alt.Chart(base)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y("Equipe:N", sort="-x", title=None),
            x=alt.X("Indice discipline:Q", title="Cartons pondérés par match"),
            color=couleur_barre,
            tooltip=[
                alt.Tooltip("Equipe:N", title="Équipe"),
                alt.Tooltip("Indice discipline:Q", format=".2f"),
                alt.Tooltip("Jaunes:Q"),
                alt.Tooltip("Rouges:Q"),
                alt.Tooltip("Points:Q"),
            ],
        )
    )
    regle_moy = (
        alt.Chart(pd.DataFrame({"x": [moy_disc], "label": [f"Moyenne ligue {moy_disc:.2f}"]}))
        .mark_rule(strokeDash=[4, 4], color=COULEUR_LIGUE, strokeWidth=2)
        .encode(x="x:Q", tooltip=alt.Tooltip("label:N", title=""))
    )
    st.altair_chart((barres + regle_moy).properties(height=520), width="stretch")
    st.caption(
        "Barres horizontales triées : la comparaison d'une seule mesure entre 20 équipes se lit de haut en bas. "
        "La ligne orange est la moyenne de la ligue. Une équipe au-dessus prend plus de cartons que la moyenne."
    )

st.divider()
st.page_link("pages/2_Detail_equipe.py", label="Voir la trajectoire de l'équipe sur 5 saisons et le domicile / extérieur", icon="➡️")
