import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Rubi&Gabi",
    page_icon="💰",
    layout="wide"
)

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
body, .stApp {
    background-color: #2f3a4a;
    color: white;
    font-family: Arial;
}

h1, h2, h3 {
    text-align: center;
    color: #38bdf8;
}

div[data-testid="metric-container"] {
    background-color: #3e4b5c;
    border-radius: 14px;
    padding: 16px;
}

div[data-testid="metric-container"]:hover {
    transform: scale(1.02);
    transition: 0.2s;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DADOS
# =========================
if "data" not in st.session_state:
    st.session_state.data = []

# =========================
# TÍTULO
# =========================
st.title("💰 Rubi&Gabi")

# =========================
# INPUT
# =========================
colA, colB = st.columns(2)

with colA:
    pessoa = st.radio("Pessoa", ["Ruben", "Gabi"], horizontal=True)
    tipo = st.radio("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"], horizontal=True)

categoria = ""
descricao = ""

with colB:
    if tipo == "Despesa":
        categoria = st.radio(
            "Categoria",
            ["Renda", "Água", "Luz", "Vodafone", "Alimentação", "Gasolina", "Outros"],
            horizontal=True
        )

        if categoria == "Outros":
            descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

# =========================
# ADICIONAR
# =========================
if st.button("Adicionar"):
    st.session_state.data.append({
        "Pessoa": pessoa,
        "Tipo": tipo,
        "Categoria": categoria,
        "Descrição": descricao,
        "Valor": valor,
        "Data": data,
        "Ano": data.year,
        "Mês": data.month
    })
    st.success("Adicionado 👍")

# =========================
# DATAFRAME
# =========================
df = pd.DataFrame(st.session_state.data)

# =========================
# RESUMO
# =========================
st.subheader("📊 Resumo")

if not df.empty:

    rend = df[df["Tipo"].isin(["Salário", "Subsídio Alimentação"])]["Valor"].sum()
    desp = df[df["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = rend - desp

    c1, c2, c3 = st.columns(3)

    c1.metric("💵 Rendimentos", f"€ {rend:.2f}")
    c2.metric("🧾 Despesas", f"€ {desp:.2f}")
    c3.metric("📈 Saldo", f"€ {saldo:.2f}")

    if rend > 0:
        ratio = desp / rend

        if ratio >= 1:
            st.error("🚨 Gastaste mais do que ganhaste!")
        elif ratio >= 0.8:
            st.warning("⚠️ Quase a atingir o limite (80%)")
        else:
            st.success("✅ Finanças equilibradas")

# =========================
# FILTRO
# =========================
if not df.empty:
    pessoa_sel = st.selectbox("Filtrar:", ["Todos", "Ruben", "Gabi"])
    if pessoa_sel != "Todos":
        df = df[df["Pessoa"] == pessoa_sel]

# =========================
# GRÁFICO MENSAL (FIX 1–12)
# =========================
if not df.empty:

    st.subheader("📊 Evolução Mensal")

    # garantir inteiro
    df["Mês"] = df["Mês"].astype(int)

    mensal = df.groupby("Mês")["Valor"].sum().reset_index()
    mensal = mensal.sort_values("Mês")

    fig = px.bar(
        mensal,
        x="Mês",
        y="Valor",
        text="Valor"
    )

    fig.update_xaxes(
        tickmode="linear",
        dtick=1
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================
# DESPESAS
# =========================
if not df.empty:

    st.subheader("📊 Despesas por Categoria")

    despesas = df[df["Tipo"] == "Despesa"]

    fig2 = px.pie(despesas, values="Valor", names="Categoria")
    st.plotly_chart(fig2, use_container_width=True)

# =========================
# HISTÓRICO
# =========================
st.subheader("📅 Histórico")

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Sem dados ainda.")
