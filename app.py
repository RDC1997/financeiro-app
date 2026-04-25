import streamlit as st
import pandas as pd
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(page_title="Rubi&Gabi Finance", layout="wide")
st.title("💰 Controlo Financeiro")

# =========================
# GOOGLE SHEETS
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").sheet1

except Exception as e:
    st.error("❌ Erro ao ligar ao Google Sheets")
    st.stop()

# =========================
# DATA
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(raw[1:], columns=raw[0])
    df.columns = df.columns.str.strip()

    df["Pessoa"] = df["Pessoa"].astype(str).str.strip()
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

    # 🔥 DATA SEM HORA (CORREÇÃO)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date

    df["sheet_row"] = df.index + 2

    return df

df = load_data()

# =========================
# ICONS
# =========================
icons = {
    "Renda": "🏠",
    "Vodafone": "📱",
    "Gasolina": "🚗",
    "Alimentação": "🛒",
    "Luz": "💡",
    "Água": "🚿",
    "Outros": "📦"
}

avatars = {
    "Ruben": "🤴",
    "Gabi": "👸"
}

# =========================
# MODO
# =========================
modo = st.sidebar.selectbox("Modo", ["Casal", "Ruben", "Gabi", "Todos"])

# =========================
# 🟣 TODOS (SEPARADO POR PESSOA)
# =========================
if modo == "Todos":

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = df[df["Pessoa"] == pessoa]

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        # =========================
        # RECEITAS
        # =========================
        st.markdown("### 💰 Receitas")
        if not receitas.empty:
            st.table(
                receitas[["Tipo","Valor","Data"]]
            )
        else:
            st.info("Sem receitas")

        # =========================
        # DESPESAS
        # =========================
        st.markdown("### 💸 Despesas")
        if not despesas.empty:

            despesas = despesas.copy()

            despesas["Categoria"] = despesas.apply(
                lambda r: f"{icons.get(r['Categoria'],'')} {r['Categoria']} - {r['Descrição']}"
                if r["Categoria"] == "Outros"
                else f"{icons.get(r['Categoria'],'')} {r['Categoria']}",
                axis=1
            )

            st.table(
                despesas[["Categoria","Valor","Data"]]
            )
        else:
            st.info("Sem despesas")

        st.markdown("---")

    st.stop()
