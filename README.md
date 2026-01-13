📊 Observatoire de la Délinquance en France — Webapp Streamlit

Ce projet propose une analyse exploratoire et interactive du taux de délinquance en France à partir de données publiques officielles.
Il combine un pipeline de nettoyage documenté, un tableau de bord Streamlit et une exploration multi-échelle (région → commune).

⚠️ **Note importante :** Le fichier `communes_clean.csv` (762 Mo) n’est pas inclus dans ce dépôt GitHub en raison de sa taille.  
Il peut être téléchargé via le lien suivant : ().

🎯 Objectifs du projet

Analyser les dynamiques territoriales et temporelles de la délinquance en France

Comparer les régions entre elles sur plusieurs années

Étudier la structure des infractions, à un niveau détaillé et via 5 grandes catégories

Permettre une exploration au niveau communal à partir du nom de la commune

Proposer une visualisation pédagogique, interactive et reproductible

🧱 Structure du projet
Projet_Data_Management/
├── notebooks/
│   └── 01_Notebook_Communes.ipynb
│   └── 02_Text_Mining.ipynb
├── data/
│   ├── communes_raw.csv
│   ├── communes_clean.csv
│   └── regions.geojson
├── streamlit/
│   ├── app.py
│   ├── utils.py
│   └── pages/
│       ├── 1_carte_interactive.py
│       └── 2_tableau_de_bord_analytique.py
├── environment.yml
├── requirements.txt
└── README.md

🔗 ACCÈS AUX JEUX DE DONNÉES :
-----------------------------
1. Dataset utilisé par l'application (Version Clean) :
https://drive.google.com/file/d/1lp3C9mCyeXONvBaMhgrS1u4n9jlBEXRi/view?usp=sharing

🔄 Préparation et nettoyage des données

Le nettoyage et la préparation des données sont réalisés dans le notebook :

📁 notebooks/01_Notebook_Communes.ipynb

Ce notebook :

nettoie les données brutes (valeurs manquantes, non diffusées) ;

harmonise les types et les libellés ;

calcule les indicateurs (taux pour 1 000 habitants, évolutions annuelles) ;

construit une catégorisation en 5 grandes classes d’infractions ;

génère les fichiers consolidés utilisés par la webapp.

👉 L’application Streamlit repose exclusivement sur les fichiers présents dans le dossier data/.

📁 Données utilisées
🔹 Données de délinquance

Source : Ministère de l’Intérieur – SSMSI

Plateforme : https://www.data.gouv.fr

Données publiques relatives aux infractions enregistrées

🔹 Données démographiques

Source : INSEE

Utilisées pour le calcul des taux pour 1 000 habitants

⚠️ Les fichiers de données brutes ne sont pas inclus dans ce dépôt en raison de leur volume.
Ils sont accessibles publiquement via les sources officielles.

⚠️ Installation des données : 
Les fichiers volumineux sont sur Drive. Pour faire fonctionner l'app :
1. Téléchargez 'communes_clean.csv' (lien dans Infos.txt).
2. Placez-le dans le dossier /Data/ à la racine du projet.

📊 Webapp Streamlit

L’application permet :

une carte interactive du taux de délinquance par région ;

des visualisations temporelles (évolution, variations annuelles) ;

des comparaisons interrégionales pour une année donnée ;

une analyse de la structure des infractions ;

une exploration via 5 grandes catégories d’infractions ;

une analyse au niveau communal, par recherche du nom de la commune.

ℹ️ À propos du code INSEE

Le code INSEE est un identifiant statistique officiel des communes, plus fiable que le code postal.
L’utilisateur n’a pas besoin de le connaître : la recherche s’effectue par nom de commune.

⚠️ Selon les données sources, certains suffixes (ex. -les-Bains, -sur-Mer) peuvent ne pas être pris en compte.

🚀 Lancer l’application en local (recommandé)

L’environnement du projet est fourni via Conda, afin de garantir la compatibilité des dépendances
(notamment pyarrow, utilisé par Streamlit).

1️⃣ Prérequis

Conda ou Miniconda installé
👉 https://docs.conda.io/en/latest/miniconda.html

2️⃣ Créer l’environnement
conda env create -f environment.yml

3️⃣ Activer l’environnement
conda activate datacom

4️⃣ Lancer l'application (depuis la racine du projet)
streamlit run 02_streamlit/app.py


L’application s’ouvre automatiquement dans le navigateur.

🌐 Déploiement (Streamlit Cloud)

L’application est compatible avec Streamlit Cloud.

Principe :

le projet est hébergé sur GitHub (dépôt public) ;

Streamlit Cloud installe automatiquement les dépendances via environment.yml ;

chaque mise à jour du dépôt déclenche un redéploiement automatique.

⚠️ Limites et précautions d’interprétation

Les données analysées correspondent aux infractions enregistrées et non à la délinquance réelle
(phénomène de sous-déclaration possible).

Certaines valeurs peuvent être absentes ou non diffusées selon les territoires et les années.

Les comparaisons territoriales doivent être interprétées avec prudence,
en l’absence de variables socio-économiques complémentaires.

👉 Ce projet vise une analyse exploratoire, non causale.

👥 Auteurs

Projet réalisé en binôme par :

Constance Keita
GitHub : https://github.com/ConstanceKEITA

Guillaume Patient
GitHub : https://github.com/patientgui

📜 Licence et usage

Les données utilisées sont publiques et soumises aux licences des plateformes sources
(data.gouv.fr, INSEE).

Le code de ce projet est fourni à des fins pédagogiques et analytiques.
