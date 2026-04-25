import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG APP
# =========================
st.set_page_config(page_title="Rubi&Gabi", layout="wide")
st.title("💰 Rubi&Gabi")

# =========================
# GOOGLE SHEETS
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME/edit"
).sheet1

# =========================
# LOAD DATA
# =========================
def load_data():
    raw = sheet.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    headers = [h.strip() for h in raw[0]]
    df = pd.DataFrame(raw[1:], columns=headers)

    df.columns = df.columns.str.strip().str.replace("\xa0", "", regex=True)

    required = ["Valor", "Mês", "Ano"]
    for col in required:
        if col not in df.columns:
            st.error(f"Coluna em falta: {col}")
            return pd.DataFrame()

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Mês"] = pd.to_numeric(df["Mês"], errors="coerce").fillna(0).astype(int)
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").fillna(0).astype(int)

    return df

# =========================
# SAVE
# =========================
def guardar(d):
    sheet.append_row([
        str(d["Pessoa"]),
        str(d["Tipo"]),
        str(d["Categoria"]),
        str(d["Descrição"]),
        float(d["Valor"]),
        str(d["Data"]),
        int(d["Mês"]),
        int(d["Ano"])
    ])

df = load_data()

# =========================
# METAS
# =========================
st.subheader("🎯 Metas")

if "metas" not in st.session_state:
    st.session_state.metas = [
        {"nome": "Casa", "valor": 10000},
        {"nome": "Carro", "valor": 5000},
        {"nome": "Poupança", "valor": 2000}
    ]

novas = []

for i, m in enumerate(st.session_state.metas):

    col1, col2 = st.columns(2)

    with col1:
        nome = st.text_input(
            "Nome",
            value=m["nome"],
            key=f"mn_{i}",
            label_visibility="collapsed"
        )

    with col2:
        val = st.number_input(
            "Valor",
            value=float(m["valor"]),
            key=f"mv_{i}"
        )

    novas.append({"nome": nome, "valor": val})

st.session_state.metas = novas

if st.button("➕ Adicionar meta"):
    st.session_state.metas.append({"nome": "Nova meta", "valor": 1000})
    st.rerun()
