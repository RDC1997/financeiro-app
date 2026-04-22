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
# GOOGLE SHEETS SETUP (CORRIGIDO)
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 🔥 AQUI ESTÁ A CORREÇÃO PRINCIPAL
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open("Financeiro Rubi&Gabi").sheet1

# =========================
# SESSION DATA
# =========================
if "data" not in st.session_state:
    st.session_state.data = []

# =========================
# INPUT FORM
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

# 👉 só mostra categoria se for despesa
if tipo == "Despesa":
    categoria = st.selectbox(
        "Categoria",
        ["Renda", "Água", "Luz", "Vodafone", "Alimentação", "Gasolina", "Outros"]
    )

    if categoria == "Outros":
        descricao = st.text_input("Descrição")

# =========================
# FUNÇÃO GOOGLE SHEETS
# =========================
def guardar(d):
    sheet.append_row([
        d["Pessoa"],
        d["Tipo"],
        d["Categoria"],
        d["Descrição"],
        d["Valor"],
        str(d["Data"]),
        d["Mês"],
        d["Ano"]
    ])

# =========================
# ADD BUTTON
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
# DATAFRAME
# =========================
df = pd.DataFrame(st.session_state.data)

# =========================
# VISÃO GERAL
# =========================
if not df.empty:

    st.subheader("📊 Visão Geral")

    total = df["Valor"].sum()

    col1, col2 = st.columns(2)
    col1.metric("Total", f"€ {total:.2f}")

    # =========================
    # RUBEN VS GABI
    # =========================
    st.subheader("⚖️ Ruben vs Gabi")

    comp = df.groupby("Pessoa")["Valor"].sum().reset_index()

    fig = px.bar(comp, x="Pessoa", y="Valor", text="Valor")
    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # GRÁFICO MENSAL
    # =========================
    st.subheader("📅 Evolução Mensal")

    mensal = df.groupby("Mês")["Valor"].sum().reset_index()

    fig2 = px.line(mensal, x="Mês", y="Valor", markers=True)
    fig2.update_xaxes(dtick=1)

    st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # TABELA
    # =========================
    st.subheader("📋 Histórico")

    st.dataframe(df, use_container_width=True)

else:
    st.info("Sem dados ainda")
