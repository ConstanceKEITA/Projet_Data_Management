import streamlit as st
import plotly.express as px

from utils import load_data, load_geojson, build_region_metrics, geojson_with_norm_names

st.set_page_config(page_title="Carte France", layout="wide")
st.title("🗺️ Carte interactive — Taux & variation (pour mille) par région")

df = load_data()
geojson = load_geojson()

st.markdown(
    """
    Cette carte représente le taux de délinquance par région, exprimé pour 1 000 habitants (‰),
    pour l’année sélectionnée.

    Chaque région est colorée en fonction de son niveau de délinquance :
    - une couleur plus foncée correspond à un taux plus élevé ;
    - une couleur plus claire correspond à un taux plus faible.

    La carte permet une **lecture spatiale immédiate** des disparités régionales
    et facilite la comparaison entre territoires pour une année donnée.

    L’utilisateur peut :
    - sélectionner l’année à analyser ;
    - survoler une région pour afficher les valeurs détaillées ;
    - observer l’évolution des contrastes régionaux en changeant d’année.

    Cette visualisation propose une **approche descriptive** et doit être interprétée
    avec prudence, les différences observées pouvant être influencées par des facteurs
    démographiques, socio-économiques ou institutionnels non pris en compte ici.
    """
)

# métriques région-année
g = build_region_metrics(df)

# geojson normalisé
gj, geo_key = geojson_with_norm_names(geojson)

# Sélecteur année
years = sorted([int(y) for y in g["annee"].dropna().unique()])
year = st.slider("Année", min_value=min(years), max_value=max(years), value=max(years))

metric = st.radio(
    "Variable à afficher",
    options=["taux_region_pour_mille", "variation_region"],
    format_func=lambda x: "Taux (pour mille)" if x == "taux_region_pour_mille" else "Variation (vs année précédente)",
    horizontal=True
)

g_y = g[g["annee"] == year].copy()

# Choroplèthe : on match via region_norm dans geojson et nom_region_norm dans data
fig = px.choropleth(
    g_y,
    geojson=gj,
    locations="nom_region_norm",
    featureidkey="properties.region_norm",
    color=metric,
    hover_name="nom_region",
    hover_data={
        "nom_region_norm": False,
        "taux_region_pour_mille": ":.2f",
        "variation_region": ":.2f",
        "nb_region": True,
        "pop_region": True,
    },
    labels={
        "taux_region_pour_mille": "Taux (%)",
        "variation_region": "Variation (%)",
    },
)

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

c1, c2 = st.columns([2, 1], vertical_alignment="top")

with c1:
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📌 Tableau (année sélectionnée)")
    st.dataframe(
        g_y[["nom_region", "annee", "taux_region_pour_mille", "variation_region", "nb_region", "pop_region"]]
          .sort_values("taux_region_pour_mille", ascending=False),
        use_container_width=True
    )






st.caption(f"Clé détectée dans le GeoJSON pour le nom de région : `{geo_key}` (normalisée en `region_norm`).")

