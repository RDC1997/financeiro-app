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

except Exception:
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

    df["Pessoa"] = df["Pessoa"].astype(str).str.strip()
    df["Tipo"] = df["Tipo"].astype(str).str.strip()
    df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df["Descrição"] = df["Descrição"].astype(str).fillna("")
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date

    return df

df = load_data()

avatars = {"Ruben":"🤴", "Gabi":"👸"}

modo = st.sidebar.selectbox("Modo", ["Casal", "Ruben", "Gabi"])

# =========================
# 🟢 CASAL
# =========================
if modo == "Casal":

    st.subheader("📊 Visão Geral")

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = df[df["Pessoa"] == pessoa]

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        # =========================
        # 💰 RECEITAS
        # =========================
        st.markdown("### 💰 Receitas")

        if not receitas.empty:
            st.dataframe(receitas[["Tipo","Valor","Data"]], use_container_width=True)
        else:
            st.info("Sem receitas")

        # =========================
        # 💸 DESPESAS
        # =========================
        st.markdown("### 💸 Despesas")

        if not despesas.empty:

            despesas = despesas.copy()

            st.dataframe(despesas[["Categoria","Valor","Data"]], use_container_width=True)

            total = despesas["Valor"].sum()
            st.markdown(f"### 💰 Total de Despesas: **€ {total:.2f}**")

        else:
            st.info("Sem despesas")

    st.stop()
