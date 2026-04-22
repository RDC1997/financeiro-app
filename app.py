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
# RESUMO BASE
# =========================
st.subheader("📊 Dashboard")

if not df.empty:

    rend = df[df["Tipo"].isin(["Salário", "Subsídio Alimentação"])]["Valor"].sum()
    desp = df[df["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = rend - desp

    ruben_total = df[df["Pessoa"] == "Ruben"]["Valor"].sum()
    gabi_total = df[df["Pessoa"] == "Gabi"]["Valor"].sum()

    diff = abs(ruben_total - gabi_total)

    # =========================
    # CARDS PRINCIPAIS
    # =========================
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("💵 Rendimentos", f"€ {rend:.2f}")
    c2.metric("🧾 Despesas", f"€ {desp:.2f}")
    c3.metric("📈 Saldo", f"€ {saldo:.2f}")
    c4.metric("⚖️ Diferença", f"€ {diff:.2f}")

    # =========================
    # ALERTAS INTELIGENTES
    # =========================
    st.subheader("🚨 Alertas")

    if rend > 0:
        ratio = desp / rend

        if ratio >= 1:
            st.error("🚨 Gastaste mais do que ganhaste!")
        elif ratio >= 0.8:
            st.warning("⚠️ Estás perto do limite (80%)")
        else:
            st.success("✅ Finanças equilibradas")

    if ruben_total > gabi_total * 1.3:
        st.error("🚨 Ruben gastou muito mais que a Gabi!")

    elif gabi_total > ruben_total * 1.3:
        st.error("🚨 Gabi gastou muito mais que o Ruben!")

    else:
        st.success("✅ Gastos equilibrados entre Ruben e Gabi")

# =========================
# FILTRO
# =========================
if not df.empty:
    pessoa_sel = st.selectbox("Filtrar:", ["Todos", "Ruben", "Gabi"])
    if pessoa_sel != "Todos":
        df = df[df["Pessoa"] == pessoa_sel]

# =========================
# GRÁFICO COMPARATIVO
# =========================
if not df.empty:

    st.subheader("📊 Comparação Ruben vs Gabi")

    compare = df.groupby("Pessoa")["Valor"].sum().reset_index()

    fig_comp = px.bar(
        compare,
        x="Pessoa",
        y="Valor",
        text="Valor"
    )

    st.plotly_chart(fig_comp, use_container_width=True)

# =========================
# GRÁFICO MENSAL
# =========================
if not df.empty:

    st.subheader("📊 Evolução Mensal")

    df["Mês"] = df["Mês"].astype(int)

    mensal = df.groupby("Mês")["Valor"].sum().reset_index()
    mensal = mensal.sort_values("Mês")

    fig = px.bar(
        mensal,
        x="Mês",
        y="Valor",
        text="Valor"
    )

    fig.update_xaxes(tickmode="linear", dtick=1)

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
