# ============================================
# 💹 risk_portefeuille.py
# Analyse professionnelle du risque d'un portefeuille avec Streamlit
# Inclut projections dans un sous-onglet
# ============================================

import pandas as pd
import yfinance as yf
import numpy as np
import streamlit as st

LOOKBACK_DAYS = 252  # Nombre de jours pour les calculs (1 an)
YEARS = [1, 5, 10, 20, 30]  # horizons de projection
SIMULATIONS = 1000           # nombre de simulations Monte Carlo

# ------------------------------
# 🔹 Fonctions utilitaires
# ------------------------------

def get_price_history(tickers, period=f"{LOOKBACK_DAYS}d"):
    price_hist = {}
    missing = []
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period)['Close']
            if not hist.empty:
                price_hist[ticker] = hist
            else:
                missing.append(ticker)
        except Exception as e:
            missing.append(ticker)
            print(f"Erreur pour {ticker}: {e}")
    df_prices = pd.DataFrame(price_hist)
    return df_prices.dropna(axis=1, how='all'), missing

def calc_volatility(returns):
    return returns.std() * np.sqrt(252)

def calc_var(series, confidence=0.95):
    return -np.percentile(series, (1-confidence)*100)

def compute_portfolio_var(returns, weights, confidence=0.95):
    portf_returns = returns[weights.index].dot(weights)
    return calc_var(portf_returns, confidence)

# ------------------------------
# 🔹 Projections (intégrées)
# ------------------------------

def show_projections(valeur_actuelle, rendement_annuel, volatilite_annuelle):
    st.markdown("### 🔮 Projections du Portefeuille")
    st.markdown(f"Valeur actuelle : **{valeur_actuelle:.2f} €**")
    st.markdown(f"Rendement annuel moyen : **{rendement_annuel:.2f} %**, Volatilité : **{volatilite_annuelle:.2f} %**")

    # Projection moyenne
    st.markdown("#### 🔹 Projection moyenne (rendement fixe)")
    proj_moy = {y: valeur_actuelle * ((1 + rendement_annuel/100)**y) for y in YEARS}
    df_moy = pd.DataFrame(list(proj_moy.items()), columns=["Années", "Valeur projetée (€)"])
    st.dataframe(df_moy.style.format("{:.2f}"))

    # Projection stochastique
    st.markdown("#### 🔹 Projection stochastique (Monte Carlo)")
    proj_stoch = {}
    for y in YEARS:
        sim_values = []
        for _ in range(SIMULATIONS):
            val = valeur_actuelle
            for _ in range(y):
                val *= 1 + np.random.normal(rendement_annuel/100, volatilite_annuelle/100)
            sim_values.append(val)
        proj_stoch[y] = {
            "Médiane": np.median(sim_values),
            "Min 5%": np.percentile(sim_values, 5),
            "Max 95%": np.percentile(sim_values, 95)
        }
    df_stoch = pd.DataFrame(proj_stoch).T.reset_index().rename(columns={"index": "Années"})
    st.dataframe(df_stoch.style.format("{:.2f}"))

    st.caption("Les projections stochastiques indiquent la médiane et l’intervalle 5-95 % des valeurs possibles.")

# ------------------------------
# 🔹 Dashboard de risque amélioré
# ------------------------------

def show_risk_dashboard(df_portfolio):
    st.markdown("### ⚠️ Analyse de Risque du Portefeuille")

    # Historique des prix
    price_df, missing_tickers = get_price_history(df_portfolio['Ticker'].tolist())
    if missing_tickers:
        st.warning(f"Aucun historique pour : {', '.join(missing_tickers)}")

    if price_df.empty:
        st.warning("Aucun historique de prix disponible pour les tickers valides.")
        return None, None, None

    returns = price_df.pct_change().dropna()
    df_valid = df_portfolio[df_portfolio['Ticker'].isin(returns.columns)].set_index('Ticker')
    weights = df_valid['Valeur totale (€)'] / df_valid['Valeur totale (€)'].sum()
    vol_annual = calc_volatility(returns[weights.index])
    var_95 = compute_portfolio_var(returns, weights, 0.95)
    var_99 = compute_portfolio_var(returns, weights, 0.99)

    # ------------------------------
    # Onglets Streamlit
    # ------------------------------
    tabs = st.tabs(["Indicateurs clés", "Synthèse par actif", "Corrélation", "Volatilité", "Projection"])

    # Indicateurs clés
    with tabs[0]:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Volatilité Moyenne", f"{vol_annual.mean()*100:.2f} %")
        col2.metric("VaR 95%", f"{var_95*100:.2f} %")
        col3.metric("VaR 99%", f"{var_99*100:.2f} %")
        col4.metric("Nb Actifs", f"{len(df_valid)}")
        vol_pond = (weights * vol_annual).sum()
        col5.metric("Volatilité Pondérée", f"{vol_pond*100:.2f} %")

    # Synthèse par actif
    with tabs[1]:
        df_summary = pd.DataFrame({
            "Valeur (€)": df_valid['Valeur totale (€)'],
            "Poids (%)": (weights * 100).round(2),
            "Volatilité (%)": (vol_annual*100).round(2),
        })
        df_summary['Poids cumulé (%)'] = df_summary['Poids (%)'].cumsum().round(2)
        df_summary = df_summary.sort_values("Poids (%)", ascending=False)
        st.table(df_summary.style.format("{:.2f}").highlight_max("Poids (%)", color="lightgreen"))

    # Corrélation
    with tabs[2]:
        corr_matrix = returns[weights.index].corr().round(2)
        st.dataframe(corr_matrix.style.background_gradient(cmap="RdYlGn", axis=None))

    # Volatilité
    with tabs[3]:
        df_vol = pd.DataFrame({
            "Volatilité (%)": (vol_annual*100).round(2),
            "Poids (%)": (weights*100).round(2)
        }).sort_values("Volatilité (%)", ascending=False)
        st.dataframe(df_vol.style.format("{:.2f}").highlight_max("Volatilité (%)", color="orange"))

    # Projection
    with tabs[4]:
        show_projections(
            valeur_actuelle=df_valid['Valeur totale (€)'].sum(),
            rendement_annuel=0,  # ou mettre un rendement estimé
            volatilite_annuelle=vol_annual.mean()*100
        )

    return vol_annual, var_95, var_99
