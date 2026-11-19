"""Application Streamlit : estimation du prix et segment d'une voiture d'occasion au Maroc.

Charge uniquement les artefacts produits par 03_regression.ipynb et
04_clustering.ipynb ; aucun entraînement ici.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

DOSSIER_ARTEFACTS = Path(__file__).resolve().parent.parent / "artifacts"


def fmt_dh(valeur):
    return f"{valeur:,.0f}".replace(",", " ") + " DH"


@st.cache_resource
def charger_artefacts():
    regression = DOSSIER_ARTEFACTS / "regression"
    clustering = DOSSIER_ARTEFACTS / "clustering"
    return {
        "modele_prix": joblib.load(regression / "modele_prix.joblib"),
        "meta_regression": json.loads((regression / "metadata.json").read_text(encoding="utf-8")),
        "pipeline_kmeans": joblib.load(clustering / "pipeline_kmeans.joblib"),
        "meta_clustering": json.loads((clustering / "segments.json").read_text(encoding="utf-8")),
    }


st.set_page_config(page_title="Prix des voitures d'occasion au Maroc", page_icon="")
st.title("Estimation du prix d'une voiture d'occasion au Maroc")
st.caption("Modèle Random Forest et segmentation K-Means entraînés sur des annonces Avito.ma (novembre 2026).")

try:
    artefacts = charger_artefacts()
except FileNotFoundError as erreur:
    st.error(
        f"Artefact introuvable : {Path(erreur.filename).name if erreur.filename else erreur}. "
        "Exécutez d'abord notebooks/03_regression.ipynb et notebooks/04_clustering.ipynb."
    )
    st.stop()
except Exception as erreur:  # artefact corrompu ou incompatible
    st.error(f"Impossible de charger les modèles : {erreur}")
    st.stop()

meta_reg = artefacts["meta_regression"]
meta_clu = artefacts["meta_clustering"]
annee_reference = meta_clu["annee_reference"]

with st.form("formulaire_voiture"):
    col1, col2 = st.columns(2)
    with col1:
        annee = st.number_input(
            "Année du véhicule",
            min_value=meta_reg["annee_min"],
            max_value=meta_reg["annee_max"],
            value=2020,
            step=1,
        )
        marque = st.selectbox("Marque", meta_reg["marques"], index=None, placeholder="Choisir une marque")
    with col2:
        kilometrage = st.number_input(
            "Kilométrage (km)",
            min_value=0,
            max_value=meta_reg["kilometrage_max"],
            value=100000,
            step=5000,
        )
        ville = st.selectbox("Ville", meta_reg["villes"], index=None, placeholder="Choisir une ville")
    km_inconnu = st.checkbox("Kilométrage inconnu")
    valider = st.form_submit_button("Estimer le prix")

if valider:
    if marque is None or ville is None:
        st.warning("Veuillez choisir une marque et une ville.")
        st.stop()
    if marque not in meta_reg["marques"] or ville not in meta_reg["villes"]:
        st.error("Marque ou ville inconnue des données d'entraînement.")
        st.stop()

    km = np.nan if km_inconnu else float(kilometrage)
    entree = pd.DataFrame(
        [{"annee": int(annee), "kilometrage": km, "marque": marque, "ville": ville}],
        columns=meta_reg["variables_entree"],
    )
    prix_predit = float(artefacts["modele_prix"].predict(entree)[0])

    # Clustering : même pipeline qu'à l'entraînement, avec le prix prédit comme prix d'entrée
    entree_clu = pd.DataFrame(
        [{"prix": prix_predit, "age": annee_reference - int(annee), "kilometrage": km}],
        columns=meta_clu["variables_entree"],
    )
    cluster = int(artefacts["pipeline_kmeans"].predict(entree_clu)[0])
    segment = meta_clu["segments"][str(cluster)]

    st.subheader("Résultat")
    st.metric("Prix estimé", fmt_dh(prix_predit))
    st.markdown(f"**Segment :** {segment['nom']}")
    st.write(segment["description"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Prix médian du segment", fmt_dh(segment["prix_median"]))
    c2.metric("Âge médian du segment", f"{segment['age_median']:.0f} ans")
    c3.metric("Km médian du segment", f"{segment['km_median_renseigne']:,.0f}".replace(",", " ") + " km")

    remarques = []
    if km_inconnu:
        km_median = f"{meta_reg['mediane_imputation_kilometrage']:,.0f}".replace(",", " ")
        remarques.append(
            "Kilométrage inconnu : il est remplacé par la médiane des données d'entraînement "
            f"({km_median} km), comme pendant l'entraînement."
        )
    if marque in meta_reg["marques_regroupees_rares"]:
        remarques.append(f"La marque {marque} est peu représentée : elle est traitée dans le groupe des marques rares.")
    if ville in meta_reg["villes_regroupees_rares"]:
        remarques.append(f"La ville {ville} est peu représentée : elle est traitée dans le groupe des villes rares.")
    for remarque in remarques:
        st.info(remarque)

    metriques = meta_reg["metriques_test"]["Random Forest (cible log)"]
    st.caption(
        f"Estimation indicative : sur le jeu de test, erreur absolue moyenne de {fmt_dh(metriques['MAE (DH)'])} "
        f"et R² de {metriques['R²']:.2f}. Le modèle ne connaît ni le modèle exact, ni l'état, ni les options du véhicule."
    )
