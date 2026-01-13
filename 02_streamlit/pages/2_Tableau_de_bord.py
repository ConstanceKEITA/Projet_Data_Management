import pandas as pd
import streamlit as st
import plotly.express as px

from utils import load_data, build_region_metrics


def guess_class_col(df: pd.DataFrame) -> str | None:
    """Détecte la colonne contenant le libellé détaillé de l’infraction/indicateur."""
    candidates = [
        "classe_infraction", "classe", "categorie", "cat", "type_infraction",
        "type", "nature", "indicateur", "libelle", "infractions", "infraction"
    ]
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in cols_lower:
            return cols_lower[cand]
    return None


def guess_commune_col(df: pd.DataFrame) -> str | None:
    """Détecte la colonne 'commune/ville' si elle existe."""
    candidates = ["nom_commune", "commune", "libelle_commune", "nom_comm", "ville", "nom_ville"]
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in cols_lower:
            return cols_lower[cand]
    return None


st.set_page_config(page_title="Tableau de Bord Analytique", layout="wide")
st.title("📈 Tableau de Bord — Analyse du taux de délinquance")

# -----------------------------
# Chargement
# -----------------------------
df = load_data()
g = build_region_metrics(df)

# -----------------------------
# 1) Courbes par région
# -----------------------------
regions = sorted(g["nom_region"].dropna().unique().tolist())
default_regions = regions[:3] if len(regions) >= 3 else regions

sel_regions = st.multiselect(
    "Régions",
    options=regions,
    default=default_regions,
    key="reg_select_main"
)

g_sel = g[g["nom_region"].isin(sel_regions)].copy()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Évolution du taux (‰) par région")
    fig1 = px.line(
        g_sel,
        x="annee",
        y="taux_region_pour_mille",
        color="nom_region",
        markers=True,
        labels={"annee": "Année", "taux_region_pour_mille": "Taux (‰)", "nom_region": "Région"},
    )
    st.plotly_chart(fig1, use_container_width=True)
    st.caption(
        "Ce graphique montre l’évolution du taux de délinquance par région au fil des années, "
        "afin d’identifier des tendances générales et des dynamiques régionales contrastées."
    )

with c2:
    st.subheader("Variation annuelle (‰) par région")
    fig2 = px.line(
        g_sel,
        x="annee",
        y="variation_region",
        color="nom_region",
        markers=True,
        labels={"annee": "Année", "variation_region": "Variation (‰)", "nom_region": "Région"},
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(
        "La variation annuelle correspond à la différence de taux entre deux années consécutives pour une même région ; "
        "elle aide à repérer les ruptures ou changements ponctuels."
    )

st.divider()

# -----------------------------
# 2) Comparaison sur une année
# -----------------------------
st.subheader("Comparaison (année au choix)")
years = sorted([int(y) for y in g["annee"].dropna().unique()])
year = st.selectbox("Année", years, index=len(years) - 1, key="cmp_year")

g_y = g[g["annee"] == year].sort_values("taux_region_pour_mille", ascending=False)

fig3 = px.bar(
    g_y,
    x="nom_region",
    y="taux_region_pour_mille",
    labels={"nom_region": "Région", "taux_region_pour_mille": "Taux (‰)"},
)
fig3.update_layout(xaxis_tickangle=-35)
st.plotly_chart(fig3, use_container_width=True)
st.caption(
    "Ce graphique compare les régions entre elles pour une année donnée : "
    "il s’agit d’une photographie des écarts régionaux de délinquance sur l’année sélectionnée."
)

with st.expander("Voir les données région-année (brutes)", expanded=False):
    st.dataframe(g.sort_values(["nom_region", "annee"]), use_container_width=True)

st.divider()

# -----------------------------
# 3) Heatmap
# -----------------------------
st.subheader("🧩 Heatmap — Taux / variation (‰) par région et par année")

metric_hm = st.radio(
    "Variable heatmap",
    ["taux_region_pour_mille", "variation_region"],
    format_func=lambda x: "Taux (‰)" if x == "taux_region_pour_mille" else "Variation (‰)",
    horizontal=True,
    key="hm_metric",
)

top_n_heat = st.slider(
    "Nombre de régions affichées (top par moyenne)",
    5, 25, 13,
    key="hm_topn"
)

pivot = g.pivot_table(
    index="nom_region",
    columns="annee",
    values=metric_hm,
    aggfunc="mean",
)

pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).head(top_n_heat).index]

fig_hm = px.imshow(
    pivot,
    labels=dict(x="Année", y="Région", color="Valeur"),
    aspect="auto",
)
st.plotly_chart(fig_hm, use_container_width=True)
st.caption(
    "La heatmap offre une lecture synthétique des niveaux (ou variations) par région et par année : "
    "elle permet d’identifier rapidement des périodes et des territoires plus élevés ou plus faibles."
)

st.divider()

# -----------------------------
# 4) Distribution (boxplot)
# -----------------------------
st.subheader("📦 Distribution — Taux (‰) par année")

fig_box = px.box(
    g.dropna(subset=["annee", "taux_region_pour_mille"]),
    x="annee",
    y="taux_region_pour_mille",
    points="outliers",
    labels={"annee": "Année", "taux_region_pour_mille": "Taux (‰)"},
)
st.plotly_chart(fig_box, use_container_width=True)
st.caption(
    "Chaque boîte correspond à une année et est construite à partir des taux de délinquance de toutes les régions. "
    "Elle résume donc la variabilité interrégionale : médiane (trait), quartiles (boîte) et dispersion (moustaches)."
)


st.divider()

# -----------------------------
# 5) Tendance lissée (moyenne mobile)
# -----------------------------
st.subheader("🧠 Tendance lissée — Moyenne mobile")

reg_roll = st.selectbox(
    "Région (lissage)",
    sorted(g["nom_region"].dropna().unique()),
    key="roll_region"
)
window = st.slider("Fenêtre (années)", 2, 5, 3, key="roll_window")

gr = g[g["nom_region"] == reg_roll].sort_values("annee").copy()
gr["taux_lisse"] = gr["taux_region_pour_mille"].rolling(window=window, min_periods=1).mean()

fig_roll = px.line(
    gr,
    x="annee",
    y=["taux_region_pour_mille", "taux_lisse"],
    markers=True,
    labels={"value": "Taux (‰)", "variable": "", "annee": "Année"},
)
st.plotly_chart(fig_roll, use_container_width=True)
st.caption(
    "La courbe lissée correspond à une moyenne mobile du taux : "
    "elle met en évidence la tendance de fond en atténuant les fluctuations d’une année à l’autre."
)

st.divider()

# -----------------------------
# 6) Répartition par type d'infraction (détaillé vs 5 classes)
# -----------------------------
st.header("🧾 Répartition par type d’infraction (détaillé vs 5 grandes classes)")

class_col = guess_class_col(df)
if class_col is None:
    st.warning(
        "Je ne trouve pas la colonne *détaillée* (ex: `indicateur`, `libelle`, etc.). "
        "Colonnes dispo : " + ", ".join(df.columns)
    )
    st.stop()

if "categorie_indicateur" not in df.columns:
    st.error("La colonne `categorie_indicateur` n’existe pas dans ton CSV nettoyé.")
    st.stop()

years_raw = sorted([int(y) for y in df["annee"].dropna().unique()])
year_rep = st.selectbox("Année", years_raw, index=len(years_raw) - 1, key="rep_year")

if "nom_region" in df.columns:
    regions_df = sorted(df["nom_region"].dropna().unique().tolist())
    region_rep = st.selectbox("Région (optionnel)", ["Toutes"] + regions_df, key="rep_region")
else:
    regions_df = []
    region_rep = "Toutes"

level = st.radio(
    "Niveau d’analyse",
    ["Détaillé", "5 grandes classes"],
    horizontal=True,
    key="rep_level",
)

group_col = class_col if level == "Détaillé" else "categorie_indicateur"

d = df[df["annee"] == year_rep].copy()
if region_rep != "Toutes":
    d = d[d["nom_region"] == region_rep]

if "nombre" not in d.columns:
    st.error("Colonne `nombre` absente : impossible de calculer la répartition.")
    st.stop()

rep = (
    d.groupby(group_col, as_index=False)
     .agg(nb=("nombre", "sum"))
     .sort_values("nb", ascending=False)
)

topn_rep = st.slider("Nombre de catégories affichées", 5, 25, 10, key="rep_topn")

if len(rep) > topn_rep:
    top = rep.head(topn_rep).copy()
    autres = rep.iloc[topn_rep:]["nb"].sum()
    top.loc[len(top)] = ["Autres", autres]
    rep_plot = top
else:
    rep_plot = rep

c1, c2 = st.columns([1.2, 1])

with c1:
    st.subheader("📊 Répartition (volumes)")
    fig_bar = px.bar(
        rep_plot,
        x=group_col,
        y="nb",
        labels={group_col: "Catégorie", "nb": "Nombre"},
    )
    fig_bar.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption("Répartition des infractions en volume pour l’année (et la région) sélectionnées.")

with c2:
    st.subheader("Structure des infractions (%)")
    fig_pie = px.pie(rep_plot, names=group_col, values="nb", hole=0.45)
    st.plotly_chart(fig_pie, use_container_width=True)
    st.caption("Poids relatif de chaque catégorie dans l’ensemble des infractions observées.")

with st.expander("Voir la table complète (année / région sélectionnées)", expanded=False):
    st.dataframe(rep, use_container_width=True)

st.divider()

# -----------------------------
# 7) Évolution de la composition (stacked)
# -----------------------------
st.header("📈 Évolution de la composition (par année)")

d2 = df.copy()

if "nom_region" in df.columns:
    region_stack = st.selectbox("Région (pour l’évolution)", ["Toutes"] + regions_df, key="stack_region")
    if region_stack != "Toutes":
        d2 = d2[d2["nom_region"] == region_stack]

group_stack = class_col if level == "Détaillé" else "categorie_indicateur"

comp = (
    d2.groupby(["annee", group_stack], as_index=False)
      .agg(nb=("nombre", "sum"))
)

if level == "Détaillé":
    topk_stack = st.slider("Nombre de catégories conservées (détaillé)", 3, 12, 6, key="stack_topk")
    top_classes = (
        comp.groupby(group_stack)["nb"].sum()
            .sort_values(ascending=False)
            .head(topk_stack)
            .index
            .tolist()
    )
    comp[group_stack] = comp[group_stack].where(comp[group_stack].isin(top_classes), "Autres")
    comp = comp.groupby(["annee", group_stack], as_index=False)["nb"].sum()

fig_area = px.area(
    comp.sort_values("annee"),
    x="annee",
    y="nb",
    color=group_stack,
    labels={"annee": "Année", "nb": "Nombre", group_stack: "Catégorie"},
)
st.plotly_chart(fig_area, use_container_width=True)
st.caption(
    "Ce graphique montre comment la **structure** des infractions évolue dans le temps : "
    "si une couleur prend plus de place, cela signifie que cette catégorie pèse davantage dans le total."
)

st.divider()

# -----------------------------
# 8) Top 20 communes
# -----------------------------
st.header("🏘️ Top 20 communes (par région et par année)")

commune_col = guess_commune_col(df)
if commune_col is None:
    st.warning("Je ne trouve pas de colonne commune dans ton CSV.\n\nColonnes dispo : " + ", ".join(df.columns))
else:
    years_c = sorted([int(y) for y in df["annee"].dropna().unique()])
    year_comm = st.selectbox("Année", years_c, index=len(years_c) - 1, key="comm_year")

    if "nom_region" in df.columns:
        regions_c = sorted(df["nom_region"].dropna().unique().tolist())
        region_comm = st.selectbox("Région", regions_c, key="comm_region")
    else:
        st.error("Colonne `nom_region` absente : impossible de filtrer par région.")
        st.stop()

    ranking_mode = st.radio("Classer par", ["Taux (‰)", "Nombre d’infractions"], horizontal=True, key="comm_rank_mode")

    dcom = df[(df["annee"] == year_comm) & (df["nom_region"] == region_comm)].copy()

    if "nombre" not in dcom.columns:
        st.error("Colonne `nombre` absente : impossible de calculer le top communes.")
        st.stop()

    has_pop = "insee_pop" in dcom.columns

    dcom_g = (
        dcom.groupby(commune_col, as_index=False)
        .agg(**{
            "nb_commune": ("nombre", "sum"),
            **({"pop_commune": ("insee_pop", "max")} if has_pop else {})
        })
    )

    if has_pop:
        dcom_g = dcom_g[dcom_g["pop_commune"] > 0].copy()
        dcom_g["taux_commune_pour_mille"] = 1000 * (dcom_g["nb_commune"] / dcom_g["pop_commune"])
    else:
        dcom_g["taux_commune_pour_mille"] = pd.NA

    if ranking_mode == "Nombre d’infractions":
        dcom_top = dcom_g.sort_values("nb_commune", ascending=False).head(20)
        y_col = "nb_commune"
        y_label = "Nombre d’infractions"
    else:
        if not has_pop:
            st.warning("Pas de colonne `insee_pop` → impossible de classer par taux. Classement par nombre.")
            dcom_top = dcom_g.sort_values("nb_commune", ascending=False).head(20)
            y_col = "nb_commune"
            y_label = "Nombre d’infractions"
        else:
            dcom_top = dcom_g.sort_values("taux_commune_pour_mille", ascending=False).head(20)
            y_col = "taux_commune_pour_mille"
            y_label = "Taux (‰)"

    fig_comm = px.bar(dcom_top, x=commune_col, y=y_col, labels={commune_col: "Commune", y_col: y_label})
    fig_comm.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig_comm, use_container_width=True)
    st.caption("Top 20 communes de la région sélectionnée (en taux ou en volume selon l’option).")

    cols_show = [commune_col, "nb_commune"]
    if has_pop:
        cols_show += ["pop_commune", "taux_commune_pour_mille"]

    st.dataframe(dcom_top[cols_show].reset_index(drop=True), use_container_width=True)

st.divider()

# -----------------------------
# 9) Recherche commune (Selectbox) — nom + code INSEE affiché
# -----------------------------
st.header("🔍 Recherche d’une commune (via selectbox)")

# Texte explicatif (UX + méthodo)
st.info(
    "ℹ️ **Recherche des communes**  \n"
    "Le code INSEE est un identifiant statistique officiel, généralement peu connu du grand public. "
    "La recherche est donc réalisée à partir du **nom de la commune**, puis l’application associe automatiquement "
    "la commune exacte et son **code INSEE** (CODGEO_2025).  \n\n"
    "⚠️ Remarque : la recherche est **souple** (insensible à la casse). Selon les sources, certaines variantes "
    "typographiques (accents, tirets, suffixes) peuvent impacter la correspondance exacte. "
    "En cas d’homonymie, le **département et la région** permettent de distinguer les communes."
)

need_cols = ["CODGEO_2025", "nom_commune", "nom_departement", "nom_region", "annee"]
missing = [c for c in need_cols if c not in df.columns]
if missing:
    st.warning("Impossible d’activer la recherche : colonnes manquantes : " + ", ".join(missing))
    st.stop()

# Table unique des communes
communes_ref = (
    df[["CODGEO_2025", "nom_commune", "nom_departement", "nom_region"]]
    .drop_duplicates()
    .copy()
)
communes_ref["label"] = communes_ref.apply(
    lambda r: f"{r['nom_commune']} ({r['nom_departement']}, {r['nom_region']}) — INSEE {r['CODGEO_2025']}",
    axis=1
)

# Filtre (pour éviter une selectbox gigantesque)
q = st.text_input(
    "Filtrer la liste (ex : Lille, Saint, Bordeaux...)",
    placeholder="Tape quelques lettres",
    key="search_filter_text"
).strip()

if q:
    options = communes_ref[communes_ref["nom_commune"].str.contains(q, case=False, na=False)]["label"].tolist()
else:
    options = communes_ref.sort_values("nom_commune")["label"].head(3000).tolist()  # limite sécurité

if not options:
    st.warning("Aucune commune trouvée avec ce filtre.")
else:
    choice = st.selectbox("Sélectionnez une commune", options=options, key="search_commune_select")

    # Extraction du code INSEE depuis le label
    insee = choice.split("INSEE ")[-1].strip()

    d0 = df[df["CODGEO_2025"].astype(str) == str(insee)].copy()

    years_s = sorted([int(y) for y in d0["annee"].dropna().unique()])
    year_s = st.selectbox("Année", years_s, index=len(years_s) - 1, key="search_year_select")

    d = d0[d0["annee"] == year_s].copy()

    st.subheader(f"📍 {d['nom_commune'].iloc[0]} — {year_s} (INSEE {insee})")

    # Fiche commune
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Région", d["nom_region"].iloc[0])
    with c2:
        st.metric("Département", d["nom_departement"].iloc[0])
    with c3:
        if "taille_commune" in d.columns:
            st.metric("Classe", d["taille_commune"].iloc[0])
    with c4:
        if "insee_pop" in d.columns and pd.notna(d["insee_pop"].iloc[0]):
            st.metric("Population", f"{int(d['insee_pop'].iloc[0]):,}".replace(",", " "))

    # Évolution du taux (si dispo)
    if "taux_calcule_pour_mille" in d0.columns:
        d0["taux_calcule_pour_mille"] = pd.to_numeric(d0["taux_calcule_pour_mille"], errors="coerce")
        evol = (
            d0.groupby("annee", as_index=False)
              .agg(taux=("taux_calcule_pour_mille", "mean"))
              .sort_values("annee")
        )
        fig_evol = px.line(evol, x="annee", y="taux", markers=True, labels={"annee": "Année", "taux": "Taux moyen (‰)"})
        st.plotly_chart(fig_evol, use_container_width=True)
        st.caption("Évolution du taux (‰) pour la commune sélectionnée (moyenne sur les indicateurs disponibles).")

    # Répartition par grandes catégories (si dispo)
    if "categorie_indicateur" in d.columns and "nombre" in d.columns:
        d["nombre"] = pd.to_numeric(d["nombre"], errors="coerce")
        repc = (
            d.groupby("categorie_indicateur", as_index=False)
             .agg(nb=("nombre", "sum"))
             .sort_values("nb", ascending=False)
        )
        fig_rep = px.bar(repc, x="categorie_indicateur", y="nb",
                         labels={"categorie_indicateur": "Catégorie", "nb": "Nombre"})
        fig_rep.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig_rep, use_container_width=True)
        st.caption("Répartition des infractions par grandes catégories (année sélectionnée).")

    with st.expander("📋 Voir toutes les lignes pour cette commune"):
        sort_cols = ["annee"]
        if "indicateur" in d0.columns:
            sort_cols.append("indicateur")
        st.dataframe(d0.sort_values(sort_cols), use_container_width=True)
