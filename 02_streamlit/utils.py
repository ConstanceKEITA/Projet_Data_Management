from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Tuple

import pandas as pd
import streamlit as st


# -----------------------------------------------------------------------------
# PATHS (robustes) - ADAPTÉS À TON ARBORESCENCE
# -----------------------------------------------------------------------------
def get_project_paths(
    base_dir: Path | None = None,
    data_dirname: str = "Data",  # ✅ ton dossier s'appelle "Data" (majuscule)
    data_filename: str = "communes_clean.csv",
    geojson_filename: str = "regions.geojson",
) -> tuple[Path, Path]:
    """
    Retourne (data_path, geojson_path) avec chemins robustes.

    Ta structure :
    PROJET DATA/
      Data/
        communes_clean.csv
        regions.geojson
      streamlit/
        utils.py
        app.py
        pages/
          ...
    """
    if base_dir is None:
        # utils.py est dans .../PROJET DATA/streamlit/utils.py
        # racine projet = .../PROJET DATA
        base_dir = Path(__file__).resolve().parents[1]

    data_dir = base_dir / data_dirname
    data_path = data_dir / data_filename
    geojson_path = data_dir / geojson_filename
    return data_path, geojson_path


# -----------------------------------------------------------------------------
# NORMALISATION
# -----------------------------------------------------------------------------
def norm_str(s: str) -> str:
    """Normalise une chaîne (sans accents, minuscules, espaces clean)."""
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # remove accents
    s = " ".join(s.split())
    return s


def guess_geojson_region_key(geojson: dict) -> str:
    """Devine la clé contenant le nom de région dans properties."""
    features = geojson.get("features", [])
    if not features:
        return "nom"

    props = features[0].get("properties", {}) or {}
    candidates = [
        "nom", "Nom", "NOM",
        "name", "Name", "NAME",
        "region", "REGION",
        "libelle", "LIBELLE",
        "nom_region", "NOM_REGION",
    ]
    for k in candidates:
        if k in props:
            return k

    # fallback : première propriété texte
    for k, v in props.items():
        if isinstance(v, str) and v.strip():
            return k

    return list(props.keys())[0] if props else "nom"


# -----------------------------------------------------------------------------
# LOADERS (Streamlit cache)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(data_path: Path | None = None) -> pd.DataFrame:
    """
    Charge le CSV et prépare les colonnes nécessaires.
    Si data_path est None, utilise get_project_paths().
    """
    if data_path is None:
        data_path, _ = get_project_paths()

    if not data_path.exists():
        raise FileNotFoundError(
            f"CSV introuvable : {data_path}\n"
            f"(Vérifie que le fichier est bien dans PROJET DATA/Data/)"
        )

    df = pd.read_csv(data_path, sep=",", dtype={0: str, "CODGEO_2025": str}, low_memory=False)

    if "annee" in df.columns:
        df["annee"] = pd.to_numeric(df.get("annee"), errors="coerce").astype("Int64")

    for c in ["nombre", "insee_pop"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # On retire les lignes non diffusées
    if "nombre" in df.columns and "insee_pop" in df.columns:
        df = df[df["nombre"].notna() & df["insee_pop"].notna()]

    # Normalisation région
    if "nom_region" in df.columns:
        df["nom_region_norm"] = df["nom_region"].map(norm_str)

    return df


@st.cache_data(show_spinner=False)
def load_geojson(geojson_path: Path | None = None) -> dict:
    """
    Charge le GeoJSON (texte -> dict) de façon stable pour le cache.
    Si geojson_path est None, utilise get_project_paths().
    """
    if geojson_path is None:
        _, geojson_path = get_project_paths()

    if not geojson_path.exists():
        raise FileNotFoundError(
            f"GeoJSON introuvable : {geojson_path}\n"
            f"(Vérifie que le fichier est bien dans PROJET DATA/Data/)"
        )

    text = geojson_path.read_text(encoding="utf-8")
    return json.loads(text)


@st.cache_data(show_spinner=False)
def geojson_with_norm_names(geojson: dict) -> Tuple[dict, str]:
    """
    Ajoute properties['region_norm'] dans chaque feature pour faciliter le merge Plotly.
    Retourne (geojson_modifié, clé_detectée_du_nom_de_région).
    """
    gj = json.loads(json.dumps(geojson))  # deep copy safe
    key = guess_geojson_region_key(gj)

    for feat in gj.get("features", []):
        props = feat.setdefault("properties", {})
        props["region_norm"] = norm_str(props.get(key, ""))

    return gj, key


# -----------------------------------------------------------------------------
# METRICS
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def build_region_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Table région-année :
    - nb_region (somme 'nombre')
    - pop_region (somme 'insee_pop')
    - taux_region_pour_mille = 1000 * nb/pop
    - variation_region = diff annuelle du taux par région
    """
    required = {"nom_region", "nom_region_norm", "annee", "nombre", "insee_pop"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Colonnes manquantes dans le CSV : {missing}")

    g = (
        df.groupby(["nom_region", "nom_region_norm", "annee"], as_index=False)
          .agg(
              nb_region=("nombre", "sum"),
              pop_region=("insee_pop", "sum"),
          )
    )

    g["pop_region"] = g["pop_region"].replace({0: pd.NA})
    g["taux_region_pour_mille"] = 1000 * (g["nb_region"] / g["pop_region"])

    g = g.sort_values(["nom_region", "annee"])
    g["variation_region"] = (
        g.groupby("nom_region")["taux_region_pour_mille"]
         .diff()
         .fillna(0)
    )
    return g


# -----------------------------------------------------------------------------
# OPTIONAL: quick diagnostics for matching
# -----------------------------------------------------------------------------
def compute_matching_diagnostics(g_y: pd.DataFrame, geojson_norm: dict) -> dict:
    """
    Donne des infos pour vérifier si le merge CSV ↔ GeoJSON match bien.
    """
    geo_regions = {
        feat.get("properties", {}).get("region_norm", "")
        for feat in geojson_norm.get("features", [])
    }
    geo_regions = {r for r in geo_regions if r}

    data_regions = set(g_y["nom_region_norm"].dropna().unique())

    missing_in_geo = sorted([r for r in data_regions if r not in geo_regions])
    missing_in_data = sorted([r for r in geo_regions if r not in data_regions])

    return {
        "n_regions_data": len(data_regions),
        "n_regions_geo": len(geo_regions),
        "missing_in_geo": missing_in_geo,
        "missing_in_data": missing_in_data,
    }
