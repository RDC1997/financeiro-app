import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Painel Financeiro", layout="wide")

# =========================
# ESTILO VISUAL
# =========================
st.title("💼 Painel Financeiro — Ruben & Gabi")

# =========================
# BASE DE DADOS
# =========================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "Pessoa", "Tipo", "Categoria", "Valor"
    ])

# =========================
# INPUTS
# =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    pessoa = st.selectbox("Pessoa", ["Ruben", "Gabi"])

with col2:
    tipo = st.selectbox("Tipo", ["Renda", "Despesa"])

with col3:
    categoria = st.selectbox("Categoria", [
        "Salário", "Cartão Alimentação", "Casa",
        "Alimentação", "Lazer", "Transporte", "Outros"
    ])

with col4:
    valor = st.number_input("Valor (€)", min_value=0.0, step=10.0)

if st.button("Adicionar"):
    st.session_state.data = pd.concat([
        st.session_state.data,
        pd.DataFrame([[pessoa, tipo, categoria, valor]],
        columns=["Pessoa", "Tipo", "Categoria", "Valor"])
    ])

# =========================
# DADOS
# =========================
df = st.session_state.data

# =========================
# MÉTRICAS
# =========================
rendas = df[df["Tipo"] == "Renda"]["Valor"].sum()
despesas = df[df["Tipo"] == "Despesa"]["Valor"].sum()
saldo = rendas - despesas

c1, c2, c3 = st.columns(3)

c1.metric("💰 Rendas", f"€ {rendas:,.2f}")
c2.metric("💸 Despesas", f"€ {despesas:,.2f}")
c3.metric("⚖️ Saldo", f"€ {saldo:,.2f}")

# =========================
# GRÁFICO
# =========================
st.subheader("📊 Distribuição Financeira")

if not df.empty:
    fig = px.pie(df, values="Valor", names="Categoria", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

# =========================
# TABELA
# =========================
st.subheader("📋 Movimentos")

st.dataframe(df, use_container_width=True)

# =========================
# FILTRO POR PESSOA
# =========================
st.subheader("👨‍👩‍👧‍👦 Análise por Pessoa")

pessoa_sel = st.selectbox("Selecionar", ["Ruben", "Gabi"])

df_pessoa = df[df["Pessoa"] == pessoa_sel]

st.write("💰 Total:", df_pessoa[df_pessoa["Tipo"]=="Renda"]["Valor"].sum())
st.write("💸 Despesas:", df_pessoa[df_pessoa["Tipo"]=="Despesa"]["Valor"].sum())