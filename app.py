import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Gestão Rubi&Gabi PRO",
    page_icon="💰",
    layout="wide"
)

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
body {
    background-color: #2b3441;
    color: white;
}

.stApp {
    background-color: #2b3441;
    color: white;
}

h1, h2, h3 {
    text-align: center;
    color: #38bdf8;
}

/* cards */
div[data-testid="metric-container"] {
    background-color: #3a4656;
    border-radius: 14px;
    padding: 14px;
    transition: 0.3s;
}

div[data-testid="metric-container"]:hover {
    transform: scale(1.02);
    background-color: #44536a;
}
</style>
""", unsafe_allow_html=True)

# =========================
# FICHEIRO DE DADOS (MEMÓRIA)
# =========================
FILE = "dados_financeiros.csv"

def load_data():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)
    else:
        return pd.DataFrame(columns=[
            "Pessoa","Tipo","Categoria","Descrição",
            "Valor","Data","Ano","Mês"
        ])

def save_data(df):
    df.to_csv(FILE, index=False)

df = load_data()

# =========================
# TÍTULO
# =========================
st.title("💰 Gestão Rubi&Gabi PRO")

# =========================
# INPUT
# =========================
st.subheader("➕ Novo movimento")

pessoa = st.radio("Pessoa", ["Ruben", "Gabi"], horizontal=True)
tipo = st.radio("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"], horizontal=True)

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.radio(
        "Categoria",
        ["Renda", "Água", "Luz", "Vodafone", "Alimentação", "Gasolina", "Outros"],
        horizontal=True
    )

    if categoria == "Outros":
        descricao = st.text_input("📝 Descrição")

valor = st.number_input("Valor (€)", min_value=0.0, step=10.0)
data = st.date_input("Data", datetime.today())

# =========================
# ADICIONAR
# =========================
if st.button("Adicionar"):

    novo = {
        "Pessoa": pessoa,
        "Tipo": tipo,
        "Categoria": categoria,
        "Descrição": descricao,
        "Valor": valor,
        "Data": data,
        "Ano": data.year,
        "Mês": data.month
    }

    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    save_data(df)

    st.success("Guardado com sucesso 👍")

# =========================
# FILTRO PESSOA
# =========================
if not df.empty:
    pessoa_sel = st.selectbox("Ver dados de:", ["Todos", "Ruben", "Gabi"])
    if pessoa_sel != "Todos":
        df = df[df["Pessoa"] == pessoa_sel]

# =========================
# RESUMO
# =========================
st.subheader("📊 Resumo Financeiro")

if not df.empty:

    rend = df[df["Tipo"].isin(["Salário", "Subsídio Alimentação"])]["Valor"].sum()
    desp = df[df["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = rend - desp

    col1, col2, col3 = st.columns(3)

    col1.metric("💵 Rendimentos", f"€ {rend:.2f}")
    col2.metric("🧾 Despesas", f"€ {desp:.2f}")
    col3.metric("📈 Saldo", f"€ {saldo:.2f}")

# =========================
# GRÁFICO MENSAL (ORDENADO)
# =========================
if not df.empty:

    st.subheader("📊 Evolução Mensal")

    mensal = df.groupby("Mês")["Valor"].sum().reset_index()

    fig = px.bar(
        mensal,
        x="Mês",
        y="Valor",
        text="Valor"
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================
# DESPESAS
# =========================
if not df.empty:

    st.subheader("📊 Despesas por Categoria")

    despesas = df[df["Tipo"] == "Despesa"]

    fig2 = px.pie(
        despesas,
        values="Valor",
        names="Categoria"
    )

    st.plotly_chart(fig2, use_container_width=True)

# =========================
# HISTÓRICO
# =========================
st.subheader("📅 Histórico Completo")

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Sem dados ainda.")
