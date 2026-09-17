"""
Page méthode : définitions des KPI, hypothèses, source et limites.
"""

import streamlit as st

from utils import POIDS_JAUNE, POIDS_ROUGE, charger_matchs, ecarts_top_bas

st.title("Méthode, définitions et limites")

df = charger_matchs()
nb_matchs = f"{len(df):,}".replace(",", " ")
st.markdown(
    f"""
### Données
- Source : [football-data.co.uk](https://www.football-data.co.uk), division E0 (Premier League), fichiers bruts dans `data/`.
- {nb_matchs} matchs sur 5 saisons complètes (2019-20 à 2023-24), 380 matchs par saison, aucune valeur manquante
  sur les colonnes utilisées (contrôle fait dans le notebook d'analyse exploratoire).
- Chaque match est vu deux fois dans le dashboard : une fois du point de vue de l'équipe à domicile, une fois de celle à l'extérieur
  (3 800 lignes équipe × match).

### Les trois KPI

| KPI | Formule | Pourquoi actionnable | Vanity metric évitée |
|---|---|---|---|
| Taux de cadrage | tirs cadrés / tirs tentés | Se travaille en finition et en sélection de tir. L'analyse exploratoire a montré qu'à tirs cadrés constants, tirer plus ne rapporte rien. | Nombre de tirs |
| Taux de conversion | buts / tirs cadrés | Isole la finition et la qualité des occasions. C'est le meilleur des trois KPI pour expliquer les points (corrélation 0,65 sur 100 saisons-équipes). | Nombre de buts |
| Indice discipline | (jaunes × {POIDS_JAUNE} + rouges × {POIDS_ROUGE}) / matchs | L'ACP du notebook a montré que la discipline est indépendante de la domination offensive : le staff peut la travailler comme un chantier séparé. | Nombre de fautes |

Les ratios sont calculés sur les sommes (buts totaux / tirs cadrés totaux) et non en moyenne des ratios par match :
un match à 0 tir cadré ne fausse donc rien.

### Pourquoi un carton rouge vaut 3
Le dataset donne le nombre de cartons, pas leur motif ni le joueur. Il est donc impossible de calculer le vrai nombre de matchs de suspension.
Barème de la FA pour un rouge direct : 1 match pour un deuxième jaune ou une occasion de but annihilée, 2 matchs pour contestation,
3 matchs minimum pour conduite violente ou faute grossière. Le poids 3 correspond à la sanction standard la plus lourde
et suit la logique des classements fair-play. C'est une hypothèse, affichée comme telle. Avec un poids de 1 ou de 2, le classement
disciplinaire des équipes change à la marge mais pas l'écart top 6 / relégués.

### Le message clé, chiffré
"""
)
ecarts = ecarts_top_bas().rename(columns={"Taux de cadrage": "Cadrage", "Taux de conversion": "Conversion", "Indice discipline": "Discipline"})
st.dataframe(
    ecarts.style.format({"Cadrage": "{:.1%}", "Conversion": "{:.1%}", "Discipline": "{:.2f}"}),
    width="content",
)
st.caption("Top 6 = les 6 premiers de chaque saison, relégués = les 3 derniers. Moyenne sur les 5 saisons, tous matchs confondus.")

st.markdown(
    """
### Limites
- Pas de xG (expected goals) : le taux de conversion mélange la qualité des occasions et la finition.
- Pas de données individuelles : l'indice disciplinaire ne dit pas qui prend les cartons ni combien de matchs de suspension en découlent.
- La saison 2020-21 s'est jouée à huis clos : l'écart domicile / extérieur y est atypique.
- La hausse générale de l'indice disciplinaire en 2023-24 tient aussi à un changement d'arbitrage (sanctions plus fréquentes
  pour perte de temps et contestation), pas seulement au comportement des équipes.
- Les tirs cadrés de football-data.co.uk sont comptés par un fournisseur tiers : un but contre son camp n'est pas un tir cadré,
  d'où quelques matchs où la conversion dépasse 100 %.
"""
)
