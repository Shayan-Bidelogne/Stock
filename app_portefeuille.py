# ============================================================
# 💼 app_portefeuille.py
# Tableau de bord Streamlit avec sous-onglets pour portefeuille/risque/projection
# ============================================================

import os
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px
import streamlit as st
import risk_portefeuille as risk        # module risque

# ------------------------------
# ⚙️ CONFIGURATION GÉNÉRALE
# ------------------------------
st.set_page_config(page_title="Suivi de Portefeuille", page_icon="💼", layout="wide")

if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("💼 Tableau de Bord - Gestion de Portefeuille")
st.markdown("_Suivi professionnel des performances, allocations, risques et projections._")

# ------------------------------
# 📂 CONSTANTES
# ------------------------------
PORTEFEUILLE_FILE = "C:/Users/shaya/OneDrive/Desktop/cv-shayan/assets/portefeuille.txt"

# ------------------------------
# 📊 FONCTIONS PORTFOLIO
# ------------------------------
def lire_portefeuille(file_path: str) -> pd.DataFrame:
    data = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("/")
            ticker = parts[0]
            prix_entree = float(parts[1])
            quantite = float(parts[2])
            dividende_unitaire = float(parts[3]) if len(parts) > 3 else 0
            dividende_total = dividende_unitaire * quantite
            data.append([ticker, prix_entree, quantite, dividende_total])
    return pd.DataFrame(
        data,
        columns=["Ticker", "Prix d'achat (€)", "Quantité", "Dividendes totaux (€)"],
    )

def get_current_price(ticker: str):
    try:
        return yf.Ticker(ticker).history(period="1d")["Close"][-1]
    except Exception:
        return None

def calculs_financiers(df: pd.DataFrame) -> pd.DataFrame:
    df["Cours actuel (€)"] = df["Ticker"].apply(get_current_price)
    df["Valeur totale (€)"] = df["Cours actuel (€)"] * df["Quantité"]
    df["Performance (%)"] = ((df["Cours actuel (€)"] - df["Prix d'achat (€)"]) / df["Prix d'achat (€)"] * 100).round(2)
    df["Rendement sur coût (%)"] = (df["Dividendes totaux (€)"] / (df["Prix d'achat (€)"] * df["Quantité"]) * 100).round(2)
    return df

def synthese_portefeuille(df: pd.DataFrame):
    montant_investi_total = (df["Prix d'achat (€)"] * df["Quantité"]).sum()
    valeur_actuelle_totale = df["Valeur totale (€)"].sum()
    performance_totale = ((valeur_actuelle_totale - montant_investi_total) / montant_investi_total * 100).round(2)
    dividendes_totaux = df["Dividendes totaux (€)"].sum()
    rendement_moyen_cout = (dividendes_totaux / montant_investi_total * 100).round(2)
    df["Poids (%)"] = (df["Valeur totale (€)"] / valeur_actuelle_totale * 100).round(2)
    return montant_investi_total, valeur_actuelle_totale, performance_totale, dividendes_totaux, rendement_moyen_cout

# ------------------------------
# 📌 FONCTIONS D’AFFICHAGE
# ------------------------------
def afficher_tableau(df: pd.DataFrame):
    df_display = df.copy()
    for col in ["Prix d'achat (€)", "Cours actuel (€)", "Valeur totale (€)", "Dividendes totaux (€)"]:
        df_display[col] = df_display[col].apply(lambda x: f"{x:.2f} €")
    for col in ["Performance (%)", "Rendement sur coût (%)", "Poids (%)"]:
        df_display[col] = df_display[col].apply(lambda x: f"{x:.2f} %")

    def color_percent(val):
        try:
            num = float(val.replace("%",""))
            if num > 0:
                return "background-color: rgba(0,255,0,0.15); color:#4CAF50; font-weight:600;"
            elif num == 0:
                return "background-color: rgba(255,165,0,0.15); color:orange; font-weight:600;"
            else:
                return "background-color: rgba(255,0,0,0.15); color:#E53935; font-weight:600;"
        except Exception:
            return ""
    styled_df = df_display.style.applymap(color_percent, subset=["Performance (%)","Rendement sur coût (%)"])
    st.dataframe(styled_df, use_container_width=True)

def afficher_repartition(df: pd.DataFrame):
    st.markdown("### 🥧 Répartition du Portefeuille")
    df_sorted = df.sort_values(by="Valeur totale (€)", ascending=False)
    fig = px.pie(df_sorted, names="Ticker", values="Valeur totale (€)", hole=0.3)
    fig.update_traces(textposition="inside", textinfo="label+percent")
    st.plotly_chart(fig, use_container_width=True)

def afficher_synthese(montant, valeur, perf, dividendes, rendement):
    st.markdown("---")
    st.markdown("### 💰 Synthèse Globale")
    col1, col2, col3 = st.columns(3)
    col1.metric("Montant investi total", f"{montant:.2f} €")
    col2.metric("Valeur actuelle totale", f"{valeur:.2f} €", f"{perf:.2f} %")
    col3.metric("Performance totale", f"{perf:.2f} %")
    st.markdown("### 💶 Synthèse Dividendes")
    col4, col5 = st.columns(2)
    col4.metric("Dividendes totaux encaissés", f"{dividendes:.2f} €")
    col5.metric("Rendement sur coût moyen", f"{rendement:.2f} %")

def afficher_evolution(valeur_actuelle):
    st.markdown("---")
    st.markdown("### 📈 Évolution du Portefeuille dans le Temps")
    histo_df = pd.DataFrame({"Date":[datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                             "Valeur_totale":[valeur_actuelle]})
    st.metric("Valeur actuelle du portefeuille", f"{valeur_actuelle:.2f} €")
    st.line_chart(histo_df.set_index("Date")["Valeur_totale"])

# ------------------------------
# 🚀 EXÉCUTION PRINCIPALE
# ------------------------------
def main():
    df = lire_portefeuille(PORTEFEUILLE_FILE)
    df = calculs_financiers(df)
    montant, valeur, perf, dividendes, rendement = synthese_portefeuille(df)

    tab1, tab2, tab3 = st.tabs(["Portefeuille", "Risque", "Projection"])

    # ------------------------------
    # Onglet Portefeuille
    # ------------------------------
    with tab1:
        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
            "Détails par ligne", "Répartition", "Synthèse globale", "Évolution"
        ])
        with sub_tab1: afficher_tableau(df)
        with sub_tab2: afficher_repartition(df)
        with sub_tab3: afficher_synthese(montant, valeur, perf, dividendes, rendement)
        with sub_tab4: afficher_evolution(valeur)

    # ------------------------------
    # Onglet Risque
    # ------------------------------
    with tab2:
        df_portfolio = df[['Ticker', 'Valeur totale (€)']]
        risk.show_risk_dashboard(df_portfolio)


if __name__ == "__main__":
    main()
