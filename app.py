import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="Rubi&Gabi", layout="wide")
st.title("💰 Rubi&Gabi")

# =========================
# GOOGLE SHEETS AUTH
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
# DATA SESSION
# =========================
if "data" not in st.session_state:
    st.session_state.data = []

# =========================
# INPUT
# =========================
st.subheader("➕ Novo registo")

col1, col2 = st.columns(2)

with col1:
    pessoa = st.selectbox("Pessoa", ["Ruben", "Gabi"])
    tipo = st.selectbox("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"])

with col2:
    valor = st.number_input("Valor (€)", min_value=0.0, step=10.0)
    data = st.date_input("Data", datetime.today())

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox(
        "Categoria",
        ["Renda", "Água", "Luz", "Vodafone", "Alimentação", "Gasolina", "Outros"]
    )

    if categoria == "Outros":
        descricao = st.text_input("Descrição")

# =========================
# SAVE FUNCTION
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

# =========================
# BUTTON
# =========================
if st.button("Adicionar"):

    novo = {
        "Pessoa": pessoa,
        "Tipo": tipo,
        "Categoria": categoria,
        "Descrição": descricao,
        "Valor": valor,
        "Data": data,
        "Mês": data.month,
        "Ano": data.year
    }

    st.session_state.data.append(novo)
    guardar(novo)

    st.success("Guardado ☁️")

# =========================
# DASHBOARD
# =========================
df = pd.DataFrame(st.session_state.data)

if not df.empty:

    st.subheader("📊 Visão Geral")

    st.metric("Total", f"€ {df['Valor'].sum():.2f}")

    st.subheader("⚖️ Ruben vs Gabi")

    fig = px.bar(df.groupby("Pessoa")["Valor"].sum().reset_index(),
                 x="Pessoa", y="Valor", text="Valor")

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📅 Evolução Mensal")

    mensal = df.groupby("Mês")["Valor"].sum().reset_index()

    fig2 = px.line(mensal, x="Mês", y="Valor", markers=True)
    fig2.update_xaxes(dtick=1)

    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 Histórico")

    st.dataframe(df, use_container_width=True)

else:
    st.info("Sem dados ainda")
