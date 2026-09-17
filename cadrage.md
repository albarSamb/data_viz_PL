# Document de cadrage — Dashboard Premier League

**Groupe 5 · Bachelor Data et IA MD4 · Dashboards & Data Visualisation**

## Message clé

**Ce qui sépare le top 6 des relégués en Premier League, ce n'est pas le nombre de tirs mais trois choses qui se travaillent à l'entraînement : cadrer, convertir et rester discipliné.**

Sur 5 saisons (2019-20 à 2023-24, 1 900 matchs), le top 6 convertit 35,2 % de ses tirs cadrés contre 27,6 % pour les relégués, cadre 36,6 % de ses tirs contre 32,0 %, et prend 1,74 carton pondéré par match contre 2,04.

## Audience cible

**Un staff technique de club (entraîneur principal, analyste vidéo, préparateur).**
Ils n'ont pas besoin qu'on leur dise combien de buts leur équipe a marqués : ils le savent. Ils ont besoin de savoir sur quel levier travailler cette semaine et où ils se situent par rapport à la ligue. Le dashboard répond à ces deux questions en moins de 5 secondes grâce aux trois tuiles KPI avec delta.

## KPI retenus (2 offensifs, 1 disciplinaire)

| KPI | Formule | Actionnable parce que… | Vanity metric qu'il remplace |
|---|---|---|---|
| **Taux de cadrage** | tirs cadrés / tirs | Se travaille en finition et en sélection de tir. L'AED a montré qu'à tirs cadrés constants, le volume de tirs a un coefficient négatif : tirer plus sans cadrer ne rapporte rien. | Nombre de tirs |
| **Taux de conversion** | buts / tirs cadrés | Isole la finition. C'est le KPI le plus lié aux points (corrélation 0,65 sur les 100 saisons-équipes). Un club qui convertit mal sait qu'il doit travailler la finition ou la qualité des occasions, pas le pressing. | Nombre de buts |
| **Indice discipline** | (jaunes + 3 × rouges) / matchs | L'ACP de l'AED a montré que la discipline est une dimension indépendante de la domination offensive : le staff peut la travailler comme un chantier séparé sans nuire à l'attaque. La pondération 3 pour un rouge reprend la suspension standard FA pour conduite violente, hypothèse affichée dans le dashboard. | Nombre de fautes |

Les deux KPI offensifs décomposent le but en un entonnoir : tirs × cadrage × conversion = buts. Le troisième couvre l'autre dimension du jeu révélée par l'ACP. Trois KPI, deux dimensions, aucune redondance.

## Structure prévue

**Sidebar (4 filtres, communs à toutes les pages)** : saison, équipe (ou toute la ligue), lieu (tous / domicile / extérieur), et « Comparer avec » (jusqu'à 3 équipes).

**Page 1 · Synthèse**
- Titre = le message, sous-titre = les chiffres clés top 6 vs relégués.
- Zone KPI : 3 tuiles, valeur + delta vs moyenne de la ligue (ou vs saison précédente) + mini-courbe sur 5 saisons. Vert = bon sens, y compris pour la discipline où plus bas est mieux.
- Zone détail, un onglet par visualisation :
  - *Cadrage × conversion* : nuage de points des 20 équipes, taille = points au classement, équipe filtrée mise en avant, moyennes de la ligue en pointillés pour lire les quadrants.
  - *Discipline* : barres horizontales triées, équipe filtrée mise en avant, ligne de moyenne de la ligue.

**Page 2 · Détail équipe**
- L'équipe face à elle-même : trajectoire sur 5 saisons pour chaque KPI, contre la moyenne de la ligue (3 petits graphiques séparés plutôt qu'un double axe).
- L'équipe face aux autres : les équipes « Comparer avec » s'ajoutent aux courbes, et un bloc de barres par KPI les compare sur la saison filtrée, avec la moyenne de la ligue en repère.
- Domicile contre extérieur pour la saison filtrée, axes à zéro.
- Classement de la saison avec les 3 KPI, en table, pour les valeurs exactes.

**Page 3 · Méthode**
- Définitions, hypothèse de pondération, source, limites.

## Choix de conception à défendre

1. **Emphase plutôt que 20 couleurs** : l'équipe filtrée en bleu, les équipes de comparaison dans un ordre de couleurs fixe (3 max), les autres en gris. Le regard va au bon endroit et une équipe garde sa couleur d'une page à l'autre.
2. **Jamais de double axe** : les trois KPI n'ont pas la même échelle, donc trois graphiques côte à côte.
3. **Étiquettes sélectives** : sur le nuage de points, seuls les 3 premiers, les 3 derniers et l'équipe filtrée sont nommés. Le reste est dans l'infobulle.
4. **Honnêteté des échelles** : barres à zéro pour domicile / extérieur, axes tronqués uniquement sur le nuage de points où l'on compare des positions relatives, avec les moyennes de la ligue affichées comme repère.

## Technique

Streamlit multi-pages (`app.py` + `pages/`), `@st.cache_data` sur le chargement des CSV et sur la transformation équipe × match, Altair pour les graphiques (infobulles natives), données brutes football-data.co.uk dans `data/`.
