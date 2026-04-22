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

# =========================
# FILTRO
# =========================
if not df.empty:
    pessoa_sel = st.selectbox("Filtrar:", ["Todos", "Ruben", "Gabi"])
    if pessoa_sel != "Todos":
        df = df[df["Pessoa"] == pessoa_sel]

# =========================
# GRÁFICOS SEPARADOS (NOVA PARTE)
# =========================
if not df.empty:

    st.subheader("📊 Evolução Mensal por Pessoa")

    df["Mês"] = df["Mês"].astype(int)

    col1, col2 = st.columns(2)

    # ================= RUBEN =================
    ruben = df[df["Pessoa"] == "Ruben"]
    if not ruben.empty:
        mensal_ruben = ruben.groupby("Mês")["Valor"].sum().reset_index()
        mensal_ruben = mensal_ruben.sort_values("Mês")

        fig_ruben = px.bar(
            mensal_ruben,
            x="Mês",
            y="Valor",
            text="Valor",
            title="Ruben"
        )

        fig_ruben.update_xaxes(tickmode="linear", dtick=1)

        with col1:
            st.plotly_chart(fig_ruben, use_container_width=True)

    # ================= GABI =================
    gabi = df[df["Pessoa"] == "Gabi"]
    if not gabi.empty:
        mensal_gabi = gabi.groupby("Mês")["Valor"].sum().reset_index()
        mensal_gabi = mensal_gabi.sort_values("Mês")

        fig_gabi = px.bar(
            mensal_gabi,
            x="Mês",
            y="Valor",
            text="Valor",
            title="Gabi"
        )

        fig_gabi.update_xaxes(tickmode="linear", dtick=1)

        with col2:
            st.plotly_chart(fig_gabi, use_container_width=True)

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
