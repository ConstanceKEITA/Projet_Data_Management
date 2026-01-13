import streamlit as st
import pandas as pd
from utils import load_data


# -----------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Analyse Délinquance France",
    page_icon="📊",
    layout="wide",
)

# -----------------------------------------------------------------------------
# STYLE CSS (lisibilité + métriques + tableaux)
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
  /* Fond global */
  .stApp { background-color: #f6f9ff; }

  /* Lisibilité : markdown + titres (on évite de toucher aux labels) */
  .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span { color: #111827 !important; }
  h1, h2, h3, h4, h5, h6 { color: #111827 !important; }

  /* FIX: rendu des métriques (évite les "rectangles" derrière les caractères) */
  div[data-testid="stMetricLabel"],
  div[data-testid="stMetricValue"],
  div[data-testid="stMetricDelta"] {
    background: transparent !important;
    color: #111827 !important;
  }

  /* FIX TEXTE DES TABLEAUX (st.table) : empêche le texte blanc/invisible */
  div[data-testid="stTable"] table {
    color: #111827 !important;
  }
  div[data-testid="stTable"] th {
    color: #111827 !important;
    background-color: #f3f4f6 !important;
    font-weight: 600 !important;
  }
  div[data-testid="stTable"] td {
    color: #111827 !important;
    background-color: #ffffff !important;
  }

  /* Titres perso */
  .main-title { font-size: 3rem; font-weight: 800; color: #1e3a8a; margin-bottom: 10px; }
  .subtitle { font-size: 1.4rem; color: #4b5563; margin-bottom: 30px; }

  /* Cards */
  .guide-card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 10px;
    border-left: 5px solid #1e3a8a;
    height: 100%;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# CHARGEMENT DES DONNÉES
# -----------------------------------------------------------------------------
try:
    df = load_data()

    # -----------------------------------------------------------------------------
    # INTRODUCTION
    # -----------------------------------------------------------------------------
    st.markdown(
        "<div class='main-title'>📊 Observatoire de la Délinquance en France</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class='subtitle'>
Plateforme interactive d'analyse territoriale basée sur les données officielles du Ministère de l'Intérieur et de l'INSEE.
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
### 🧭 Guide d'exploration
Cette application a été conçue pour offrir plusieurs niveaux de lecture grâce à l'enrichissement de nos données :
"""
    )

    col_nav1, col_nav2, col_nav3 = st.columns(3)

    with col_nav1:
        st.markdown(
            """
<div class='guide-card'>
<strong>🌍 Analyse Spatiale</strong><br>
Cartographie interactive pour identifier les clusters de délinquance et comparer les régions.
</div>
""",
            unsafe_allow_html=True,
        )

    with col_nav2:
        st.markdown(
            """
<div class='guide-card'>
<strong>📉 Tendances & Profils</strong><br>
Étude des évolutions temporelles et analyse par <strong>taille de commune</strong> ou <strong>niveau de délinquance</strong>.
</div>
""",
            unsafe_allow_html=True,
        )

    with col_nav3:
        st.markdown(
            """
<div class='guide-card'>
<strong>🔍 Typologie des Faits</strong><br>
Exploration détaillée via la <strong>catégorisation des indicateurs</strong> (Atteintes aux biens, personnes, etc.).
</div>
""",
            unsafe_allow_html=True,
        )

    st.divider()

    # -----------------------------------------------------------------------------
    # SECTION TECHNIQUE (DATA MANAGEMENT)
    # -----------------------------------------------------------------------------
    st.header("⚙️ Caractéristiques du Dataset & Qualité")

    col1, col2, col3, col4 = st.columns(4)
    n_rows_clean = df.shape[0]

    with col1:
        st.metric("Observations Initiales", "4 714 200")
        st.caption("Volume brut SSMSI")

    with col2:
        st.metric("Données Qualifiées", f"{n_rows_clean:,}")
        st.caption("Après nettoyage et filtrage")

    with col3:
        st.metric("Variables Totales", df.shape[1])
        st.caption("Initialement : 13 colonnes")

    with col4:
        st.metric("Variables Créées", "5")
        st.caption("Numériques & Catégorielles")

    st.success(f"✅ Volume conforme : {n_rows_clean:,} lignes traitées (Seuil requis > 200 000).")

    # -----------------------------------------------------------------------------
    # DICTIONNAIRE + COMPLÉTUDE
    # -----------------------------------------------------------------------------
    with st.expander("🔍 Dictionnaire des variables et analyse de complétude"):
        missing_counts = df.isnull().sum()
        missing_pct = (missing_counts / len(df) * 100).round(2)

        desc_map = {
            "CODGEO_2025": "Code INSEE de la commune",
            "annee": "Année du recensement",
            "nombre": "Nombre de faits enregistrés",
            "taux_pour_mille": "Ratio pour 1 000 hab. (Variable créée)",
            "variation_region": "Évolution annuelle (Variable créée)",
            "niveau_delinquance": "Classement catégoriel (Faible, Moyen, Élevé)",
            "taille_commune": "Tranche de population de la commune",
            "categorie_indicateur": "Regroupement thématique des infractions",
        }

        info_df = pd.DataFrame(
            {
                "Variable": df.columns,
                "Type": df.dtypes.astype(str).values,
                "Complétude": [f"{100 - p:.1f}%" for p in missing_pct.values],
                "Signification": [desc_map.get(col, "Donnée analytique") for col in df.columns],
            }
        )

        # On garde st.table (statique) mais avec CSS correct -> texte toujours visible
        st.table(info_df.head(15))

        st.info(
            """
**Note sur les valeurs manquantes :** Les données non diffusées (NaN) représentent environ 5% des cellules totales.
Elles ont été conservées pour l'analyse de structure mais exclues des calculs de taux afin de ne pas fausser la réalité territoriale.
"""
        )

    st.divider()

    # -----------------------------------------------------------------------------
    # MÉTHODOLOGIE
    # -----------------------------------------------------------------------------
    st.subheader("🛠️ Travail de Transformation (Data Management)")
    st.markdown(
        """
Pour répondre aux objectifs d'analyse, nous avons enrichi le dataset avec 5 nouvelles variables pertinentes :

- **Variables quantitatives :** taux pour 1 000 habitants, variation annuelle.
- **Variables catégorielles :**
  - **Niveau de délinquance :** discrétisation des taux pour faciliter la lecture.
  - **Taille de commune :** segmentation pour comparer les zones urbaines et rurales.
  - **Catégorie indicateur :** regroupement des types d'infractions en grandes familles thématiques.
"""
    )

    st.divider()
    st.caption("Projet SDA 2025 | Constance Keita & Guillaume P. | Sources : SSMSI & INSEE")

except Exception as e:
    st.error(f"❌ Erreur de chargement : {e}")
