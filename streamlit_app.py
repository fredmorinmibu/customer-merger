import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz
import unidecode

# Exemple de pondération : vous pouvez ajuster selon vos besoins
COLONNE_PONDERATION = {
    "name": 2,
    "phone number": 3,
    "email": 1,
    "address": 1,
    "city": 1,
    "province": 1,
    "postal code": 1
}

def normaliser_chaine(texte, is_phone=False):
    # Convertir en minuscule, enlever les accents, stripper
    texte = unidecode.unidecode(texte.lower().strip())
    # Retirer les espaces multiples
    texte = re.sub(r"\s+", " ", texte)
    # Pour un numéro de téléphone, on enlève tous les caractères non numériques
    if is_phone:
        texte = re.sub(r"\D", "", texte)
    return texte

st.title("Détecteur de doublons avec améliorations")

# Slider pour le seuil
seuil = st.slider("Seuil de similarité (0-100)", 0, 100, 85)

# Chargement des CSV
fichier1 = st.file_uploader("Télécharger le premier CSV")
fichier2 = st.file_uploader("Télécharger le deuxième CSV")

# Colonnes possibles
colonnes_possibles = list(COLONNE_PONDERATION.keys())

# Sélecteur des colonnes à comparer
colonnes_selectionnees = st.multiselect(
    "Colonnes à comparer",
    colonnes_possibles,
    default=colonnes_possibles
)

# Sélecteur des colonnes prioritaires (déterminantes si elles dépassent le seuil)
colonnes_prioritaires = st.multiselect(
    "Colonnes prioritaires (si elles dépassent le seuil, on considère un match)",
    colonnes_selectionnees,
    default=["name", "phone number"]
)

if fichier1 and fichier2 and colonnes_selectionnees:
    # Astuce : on pourrait lire en chunks pour très gros fichiers (ex. chunksize=5000).
    # Ex. pseudo-code :
    # for chunk1 in pd.read_csv(fichier1, chunksize=5000):
    #     for chunk2 in pd.read_csv(fichier2, chunksize=5000):
    #         # Comparer chunk1 et chunk2

    # Ici, on lit tout en mémoire pour la démo
    df1 = pd.read_csv(fichier1)
    df2 = pd.read_csv(fichier2)

    resultats = []
    for idx1, row1 in df1.iterrows():
        for idx2, row2 in df2.iterrows():
            # 1) Vérifier si TOUTES les colonnes prioritaires dépassent le seuil
            prioritaire_ok = True
            for col in colonnes_prioritaires:
                val1 = normaliser_chaine(str(row1[col]), is_phone=(col=="phone number"))
                val2 = normaliser_chaine(str(row2[col]), is_phone=(col=="phone number"))
                score_p = fuzz.ratio(val1, val2)
                if score_p < seuil:
                    prioritaire_ok = False
                    break

            if prioritaire_ok and colonnes_prioritaires:
                # On calcule la moyenne des colonnes prioritaires pour info
                total_p_score = 0
                for col in colonnes_prioritaires:
                    val1 = normaliser_chaine(str(row1[col]), is_phone=(col=="phone number"))
                    val2 = normaliser_chaine(str(row2[col]), is_phone=(col=="phone number"))
                    total_p_score += fuzz.ratio(val1, val2)
                score_final = total_p_score / len(colonnes_prioritaires)

                resultats.append({
                    "Index 1": idx1,
                    "Index 2": idx2,
                    "Nom 1": row1.get("name", ""),
                    "Téléphone 1": row1.get("phone number", ""),
                    "Nom 2": row2.get("name", ""),
                    "Téléphone 2": row2.get("phone number", ""),
                    "Score": round(score_final, 2),
                    "Commentaire": "Match basé sur colonnes prioritaires"
                })
            else:
                # 2) Sinon, on effectue un score global pondéré sur toutes les colonnes sélectionnées
                total_score = 0
                total_poids = 0

                for col in colonnes_selectionnees:
                    val1 = normaliser_chaine(str(row1[col]), is_phone=(col=="phone number"))
                    val2 = normaliser_chaine(str(row2[col]), is_phone=(col=="phone number"))
                    # Score fuzzy
                    col_score = fuzz.ratio(val1, val2)
                    # Poids défini dans COLONNE_PONDERATION
                    poids = COLONNE_PONDERATION.get(col, 1)
                    total_score += col_score * poids
                    total_poids += poids

                score_global = total_score / total_poids if total_poids else 0

                if score_global >= seuil:
                    resultats.append({
                        "Index 1": idx1,
                        "Index 2": idx2,
                        "Nom 1": row1.get("name", ""),
                        "Téléphone 1": row1.get("phone number", ""),
                        "Nom 2": row2.get("name", ""),
                        "Téléphone 2": row2.get("phone number", ""),
                        "Score": round(score_global, 2),
                        "Commentaire": "Match basé sur le score pondéré"
                    })

    if resultats:
        df_resultats = pd.DataFrame(resultats)
        st.write(df_resultats)
        
        # Bouton pour télécharger les résultats en CSV
        csv = df_resultats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Télécharger le fichier CSV des doublons",
            data=csv,
            file_name="doublons.csv",
            mime="text/csv"
        )
    else:
        st.write("Aucun doublon trouvé.")
