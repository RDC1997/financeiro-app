import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from data import load_data
from utils import export_to_excel

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Finance App",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Casal"


# =========================
# LOAD DATA
# =========================
df = load_data()

if not df.empty:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")


# =========================
# NAVIGATION (CARTÕES)
# =========================
def render_nav():
    pages = [
        ("Casal", "👨‍❤️‍👩"),
        ("Ruben", "🤴"),
        ("Gabi", "👸"),
        ("Metas", "🎯"),
        ("Análises", "📊"),
    ]

    cols = st.columns(len(pages))

    for col, (name, icon) in zip(cols, pages):
        with col:
            if st.button(f"{icon} {name}", use_container_width=True):
                st.session_state.page = name


# =========================
# CASAL
# =========================
def render_casal_mode(df):
    st.subheader("👨‍❤️‍👩 Casal")

    receitas = df[df["Tipo"].isin(["Salário", "Subsídio Alimentação"])]
    despesas = df[df["Tipo"] == "Despesa"]

    total_r = receitas["Valor"].sum()
    total_d = despesas["Valor"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"{total_r:.2f} €")
    c2.metric("Despesas", f"{total_d:.2f} €")
    c3.metric("Saldo", f"{total_r - total_d:.2f} €")

    st.divider()
    st.dataframe(df.tail(10), use_container_width=True)


# =========================
# PESSOA
# =========================
def render_individual_mode(pessoa, df):
    st.subheader(pessoa)

    df_p = df[df["Pessoa"] == pessoa]

    receitas = df_p[df_p["Tipo"].isin(["Salário", "Subsídio Alimentação"])]
    despesas = df_p[df_p["Tipo"] == "Despesa"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"{receitas['Valor'].sum():.2f} €")
    c2.metric("Despesas", f"{despesas['Valor'].sum():.2f} €")
    c3.metric("Saldo", f"{receitas['Valor'].sum() - despesas['Valor'].sum():.2f} €")

    st.divider()
    st.dataframe(df_p.tail(10), use_container_width=True)


# =========================
# METAS (placeholder sem remover tua lógica futura)
# =========================
def render_metas_mode():
    st.subheader("🎯 Metas")
    st.info("Secção de metas (mantida para integração futura)")
    st.dataframe(df)


# =========================
# ANALISES
# =========================
def render_analises_mode(df):
    st.subheader("📊 Análises")

    if df.empty:
        st.warning("Sem dados")
        return

    despesas = df[df["Tipo"] == "Despesa"]

    if despesas.empty:
        st.info("Sem despesas")
        return

    cat = despesas.groupby("Categoria")["Valor"].sum()

    fig = px.pie(values=cat.values, names=cat.index)
    st.plotly_chart(fig, use_container_width=True)


# =========================
# NAV BAR
# =========================
render_nav()
st.divider()


# =========================
# ROUTER
# =========================
if st.session_state.page == "Casal":
    render_casal_mode(df)

elif st.session_state.page == "Ruben":
    render_individual_mode("Ruben", df)

elif st.session_state.page == "Gabi":
    render_individual_mode("Gabi", df)

elif st.session_state.page == "Metas":
    render_metas_mode()

elif st.session_state.page == "Análises":
    render_analises_mode(df)
