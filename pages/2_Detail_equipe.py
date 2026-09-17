"""
Page détail : une équipe comparée à elle-même (5 saisons), aux autres équipes
(filtre "Comparer avec"), au domicile / extérieur, puis le classement de la saison.
"""

import altair as alt
import pandas as pd
import streamlit as st

from utils import (
    COULEUR_EQUIPE, COULEUR_LIGUE, COULEUR_MOYENNE, PALETTE_EQUIPES, TOUTES,
    appliquer_lieu, calculer_kpis, filtres_sidebar, matchs_par_equipe,
)

df = matchs_par_equipe()
saison, equipe, lieu, comparaison = filtres_sidebar(df)
d = appliquer_lieu(df, lieu)

KPIS = ["Taux de cadrage", "Taux de conversion", "Indice discipline"]
FORMATS = {"Taux de cadrage": ".0%", "Taux de conversion": ".0%", "Indice discipline": ".2f"}
FORMATS_TOOLTIP = {"Taux de cadrage": ".1%", "Taux de conversion": ".1%", "Indice discipline": ".2f"}
MOYENNE = "Moyenne ligue"

kpi_ligue = calculer_kpis(d, ["Saison"])
kpi_equipe_saisons = calculer_kpis(d, ["Saison", "Equipe"])

# Séries affichées : l'équipe filtrée d'abord, puis les équipes de comparaison, puis la moyenne.
# Couleur fixe par position (bleu = équipe filtrée), gris pointillé = moyenne de la ligue.
equipes_series = ([equipe] if equipe != TOUTES else []) + comparaison
if equipe != TOUTES:
    couleurs_series = PALETTE_EQUIPES[:len(equipes_series)]
else:
    couleurs_series = PALETTE_EQUIPES[1:len(equipes_series) + 1]
domaine = equipes_series + [MOYENNE]
palette = couleurs_series + [COULEUR_MOYENNE]

# ----------------------------------------------------------------------------
# 1. Trajectoire sur 5 saisons : l'équipe face à elle-même, aux autres, à la ligue
# ----------------------------------------------------------------------------
if equipe == TOUTES and not comparaison:
    st.title("La ligue sur 5 saisons : la discipline décroche en 2023-24")
elif equipe == TOUTES:
    st.title(f"{', '.join(comparaison)} sur 5 saisons, face à la moyenne de la ligue")
elif comparaison:
    st.title(f"{equipe} face à {', '.join(comparaison)} sur 5 saisons")
else:
    st.title(f"{equipe} sur 5 saisons, face à la moyenne de la ligue")
if lieu != "Tous":
    st.caption(f"Matchs à {lieu.lower()} uniquement.")

ligue_long = kpi_ligue.melt(id_vars="Saison", value_vars=KPIS, var_name="KPI", value_name="Valeur")
ligue_long["Série"] = MOYENNE

eq_long = (
    kpi_equipe_saisons[kpi_equipe_saisons["Equipe"].isin(equipes_series)]
    .melt(id_vars=["Saison", "Equipe"], value_vars=KPIS, var_name="KPI", value_name="Valeur")
    .rename(columns={"Equipe": "Série"})
)
series = pd.concat([eq_long, ligue_long], ignore_index=True)

# Sans aucune équipe : bande min-max des 20 équipes pour donner l'échelle des écarts entre clubs
bande = None
if not equipes_series:
    bande = (
        kpi_equipe_saisons.groupby("Saison")[KPIS].agg(["min", "max"])
        .stack(level=0, future_stack=True).reset_index()
        .rename(columns={"level_1": "KPI"})
    )

cols = st.columns(3)
for col, kpi in zip(cols, KPIS):
    sub = series[series["KPI"] == kpi]
    lignes = (
        alt.Chart(sub)
        .mark_line(point=alt.OverlayMarkDef(size=70, filled=True), strokeWidth=2.5)
        .encode(
            x=alt.X("Saison:N", title=None, axis=alt.Axis(labelAngle=0, labelOverlap=False, labelExpr="slice(datum.label, 2)")),
            y=alt.Y("Valeur:Q", title=None, axis=alt.Axis(format=FORMATS[kpi]), scale=alt.Scale(zero=False, padding=12)),
            color=alt.Color("Série:N", scale=alt.Scale(domain=domaine, range=palette),
                            legend=alt.Legend(orient="bottom", title=None, columns=2)),
            strokeDash=alt.condition(alt.datum["Série"] == MOYENNE, alt.value([6, 4]), alt.value([1, 0])),
            tooltip=[alt.Tooltip("Série:N", title=""), alt.Tooltip("Saison:N"),
                     alt.Tooltip("Valeur:Q", title=kpi, format=FORMATS_TOOLTIP[kpi])],
        )
    )
    chart = lignes
    if bande is not None:
        b = bande[bande["KPI"] == kpi]
        aire = (
            alt.Chart(b)
            .mark_area(opacity=0.15, color=COULEUR_MOYENNE)
            .encode(x="Saison:N", y=alt.Y("min:Q"), y2="max:Q",
                    tooltip=[alt.Tooltip("Saison:N"),
                             alt.Tooltip("min:Q", title="Équipe la plus basse", format=FORMATS_TOOLTIP[kpi]),
                             alt.Tooltip("max:Q", title="Équipe la plus haute", format=FORMATS_TOOLTIP[kpi])])
        )
        chart = aire + lignes
    with col:
        st.markdown(f"**{kpi}**")
        st.altair_chart(chart.properties(height=280), width="stretch")

if not equipes_series:
    st.caption(
        "Une courbe par KPI, même axe temporel : la zone grise est l'étendue entre l'équipe la plus basse et la plus haute chaque saison. "
        "Choisissez une équipe ou ajoutez des équipes dans « Comparer avec » pour tracer leurs trajectoires."
    )
else:
    st.caption(
        "Une couleur par équipe, la moyenne de la ligue en gris pointillé. Une saison absente signifie que l'équipe n'était pas en Premier League. "
        "Trois graphiques séparés plutôt qu'un seul à deux axes, car les KPI n'ont pas la même échelle."
    )

st.divider()

# ----------------------------------------------------------------------------
# 2. Comparaison entre équipes sur la saison filtrée
# ----------------------------------------------------------------------------
st.subheader(f"Comparaison entre équipes, saison {saison}" + (f" ({lieu.lower()} uniquement)" if lieu != "Tous" else ""))
kpi_saison = calculer_kpis(d[d["Saison"] == saison], ["Equipe"])
presentes = [e for e in equipes_series if e in set(kpi_saison["Equipe"])]
absentes = [e for e in equipes_series if e not in set(kpi_saison["Equipe"])]

if not presentes:
    st.info("Choisissez une équipe dans la sidebar, ou ajoutez des équipes dans « Comparer avec », pour les comparer sur cette saison.")
else:
    comp = kpi_saison[kpi_saison["Equipe"].isin(presentes)].melt(
        id_vars=["Equipe", "Points"], value_vars=KPIS, var_name="KPI", value_name="Valeur"
    )
    moyennes = kpi_ligue.set_index("Saison").loc[saison, KPIS]
    cols = st.columns(3)
    for col, kpi in zip(cols, KPIS):
        sub = comp[comp["KPI"] == kpi]
        barres = (
            alt.Chart(sub)
            .mark_bar(cornerRadiusEnd=4, size=38)
            .encode(
                x=alt.X("Equipe:N", title=None, sort=presentes, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Valeur:Q", title=None, axis=alt.Axis(format=FORMATS[kpi])),
                color=alt.Color("Equipe:N", scale=alt.Scale(domain=domaine, range=palette), legend=None),
                tooltip=[alt.Tooltip("Equipe:N", title="Équipe"), alt.Tooltip("Points:Q"),
                         alt.Tooltip("Valeur:Q", title=kpi, format=FORMATS_TOOLTIP[kpi])],
            )
        )
        texte = (
            alt.Chart(sub)
            .mark_text(dy=-8, fontSize=12, color="#0b0b0b")
            .encode(x=alt.X("Equipe:N", sort=presentes), y="Valeur:Q",
                    text=alt.Text("Valeur:Q", format=FORMATS_TOOLTIP[kpi]))
        )
        libelle = f"Moyenne ligue {moyennes[kpi]:.2f}" if kpi == "Indice discipline" else f"Moyenne ligue {moyennes[kpi]:.1%}"
        regle = (
            alt.Chart(pd.DataFrame({"y": [moyennes[kpi]], "label": [libelle]}))
            .mark_rule(strokeDash=[6, 4], color=COULEUR_MOYENNE, strokeWidth=2)
            .encode(y="y:Q", tooltip=alt.Tooltip("label:N", title=""))
        )
        with col:
            st.markdown(f"**{kpi}**")
            st.altair_chart((barres + texte + regle).properties(height=240), width="stretch")
    st.caption(
        "Une barre par équipe, axe à zéro, ligne grise pointillée = moyenne de la ligue sur la saison. "
        "Les couleurs sont les mêmes que sur les courbes et sur le nuage de points de la synthèse."
        + (f" Non présentes en Premier League cette saison : {', '.join(absentes)}." if absentes else "")
    )

st.divider()

# ----------------------------------------------------------------------------
# 3. Domicile / extérieur sur la saison filtrée (on ignore le filtre Lieu ici, par construction)
# ----------------------------------------------------------------------------
st.subheader(f"Domicile contre extérieur, saison {saison}" + (f", {equipe}" if equipe != TOUTES else ", toute la ligue"))
src = df[df["Saison"] == saison]
if equipe != TOUTES:
    src = src[src["Equipe"] == equipe]
dom_ext = calculer_kpis(src, ["Lieu"]).melt(id_vars="Lieu", value_vars=KPIS, var_name="KPI", value_name="Valeur")

cols = st.columns(3)
for col, kpi in zip(cols, KPIS):
    sub = dom_ext[dom_ext["KPI"] == kpi]
    barres = (
        alt.Chart(sub)
        .mark_bar(cornerRadiusEnd=4, size=46)
        .encode(
            x=alt.X("Lieu:N", title=None, axis=alt.Axis(labelAngle=0), sort=["Domicile", "Extérieur"]),
            y=alt.Y("Valeur:Q", title=None, axis=alt.Axis(format=FORMATS[kpi])),
            color=alt.Color("Lieu:N", scale=alt.Scale(domain=["Domicile", "Extérieur"], range=[COULEUR_EQUIPE, COULEUR_LIGUE]), legend=None),
            tooltip=[alt.Tooltip("Lieu:N"), alt.Tooltip("Valeur:Q", title=kpi, format=FORMATS_TOOLTIP[kpi])],
        )
    )
    texte = (
        alt.Chart(sub)
        .mark_text(dy=-8, fontSize=12, color="#0b0b0b")
        .encode(x=alt.X("Lieu:N", sort=["Domicile", "Extérieur"]), y="Valeur:Q",
                text=alt.Text("Valeur:Q", format=FORMATS_TOOLTIP[kpi]))
    )
    with col:
        st.markdown(f"**{kpi}**")
        st.altair_chart((barres + texte).properties(height=220), width="stretch")
st.caption(
    "Deux barres par KPI, axe qui part de zéro : la comparaison domicile / extérieur reste honnête, un petit écart reste visuellement petit. "
    "Ce bloc ignore le filtre Lieu puisqu'il compare précisément les deux lieux."
)

st.divider()

# ----------------------------------------------------------------------------
# 4. Classement de la saison avec les 3 KPI
# ----------------------------------------------------------------------------
st.subheader(f"Classement {saison} et KPI" + (f" ({lieu.lower()} uniquement)" if lieu != "Tous" else ""))
tableau = kpi_saison.sort_values(["Points", "Buts"], ascending=False)
tableau.insert(0, "Rang", range(1, len(tableau) + 1))
tableau = tableau[["Rang", "Equipe", "Points", "Buts", "Tirs", "Tirs_cadres", "Taux de cadrage", "Taux de conversion", "Jaunes", "Rouges", "Indice discipline"]]


def surligner(ligne):
    """Équipe filtrée en bleu clair, équipes de comparaison en gris clair."""
    if ligne["Equipe"] == equipe:
        return ["background-color: #cde2fb; font-weight: bold"] * len(ligne)
    if ligne["Equipe"] in comparaison:
        return ["background-color: #f0efec; font-weight: bold"] * len(ligne)
    return [""] * len(ligne)


st.dataframe(
    tableau.style.apply(surligner, axis=1).format({
        "Taux de cadrage": "{:.1%}", "Taux de conversion": "{:.1%}", "Indice discipline": "{:.2f}",
    }),
    hide_index=True,
    height=740,
    column_config={
        "Tirs_cadres": st.column_config.NumberColumn("Tirs cadrés"),
        "Rang": st.column_config.NumberColumn(width="small"),
    },
)
st.caption("Vue table : les valeurs exactes derrière chaque graphique, pour vérification.")
