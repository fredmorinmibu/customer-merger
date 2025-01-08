import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz

def normaliser_chaine(texte, is_phone=False):
    texte = texte.lower().strip()
    # Retirer espaces multiples
    texte = re.sub(r"\s+", " ", texte)
    # Pour un numéro de téléphone, on enlève tout sauf les chiffres
    if is_phone:
        texte = re.sub(r"\D", "", texte)
    return texte

st.title("Détecteur de doublons")

# Slider pour le seuil
seuil = st.slider("Seuil de similarité (0-100)", 0, 100, 85)

# Chargement des CSV
fichier1 = st.file_uploader("Télécharger le premier CSV")
fichier2 = st.file_uploader("Télécharger le deuxième CSV")

# Colonnes possibles
colonnes_possibles = [
    "name",
    "phone number",
    "email",
    "address",
    "city",
    "province",
    "postal code",
]

# Sélecteur des colonnes à comparer
colonnes_selectionnees = st.multiselect(
    "Colonnes à comparer",
    colonnes_possibles,
    default=colonnes_possibles
)

# Sélecteur des colonnes prioritaires (parmi celles choisies)
colonnes_prioritaires = st.multiselect(
    "Colonnes prioritaires (déterminantes si elles dépassent le seuil)",
    colonnes_selectionnees,
    default=["name", "phone number"]
)

if fichier1 and fichier2 and colonnes_selectionnees:
    df1 = pd.read_csv(fichier1)
    df2 = pd.read_csv(fichier2)

    resultats = []
    for idx1, row1 in df1.iterrows():
        for idx2, row2 in df2.iterrows():
            # 1) Vérifier si TOUTES les colonnes prioritaires dépassent le seuil
            prioritaire_ok = True
            for col in colonnes_prioritaires:
                val1 = normaliser_chaine(str(row1[col]), is_phone=(col == "phone number"))
                val2 = normaliser_chaine(str(row2[col]), is_phone=(col == "phone number"))
                score_p = fuzz.ratio(val1, val2)
                if score_p < seuil:
                    prioritaire_ok = False
                    break

            if prioritaire_ok and colonnes_prioritaires:
                # Score moyen uniquement pour info (basé sur les colonnes prioritaires)
                total_p_score = 0
                for col in colonnes_prioritaires:
                    val1 = normaliser_chaine(str(row1[col]), is_phone=(col == "phone number"))
                    val2 = normaliser_chaine(str(row2[col]), is_phone=(col == "phone number"))
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
                # 2) Si on n'a pas validé toutes les colonnes prioritaires,
                # on calcule un score moyen sur toutes les colonnes sélectionnées
                total_score = 0
                for col in colonnes_selectionnees:
                    val1 = normaliser_chaine(str(row1[col]), is_phone=(col == "phone number"))
                    val2 = normaliser_chaine(str(row2[col]), is_phone=(col == "phone number"))
                    total_score += fuzz.ratio(val1, val2)
                
                score_global = total_score / len(colonnes_selectionnees)
                if score_global >= seuil:
                    resultats.append({
                        "Index 1": idx1,
                        "Index 2": idx2,
                        "Nom 1": row1.get("name", ""),
                        "Téléphone 1": row1.get("phone number", ""),
                        "Nom 2": row2.get("name", ""),
                        "Téléphone 2": row2.get("phone number", ""),
                        "Score": round(score_global, 2),
                        "Commentaire": "Match basé sur la moyenne de toutes les colonnes sélectionnées"
                    })

    if resultats:
        st.write(pd.DataFrame(resultats))
    else:
        st.write("Aucun doublon trouvé.")
