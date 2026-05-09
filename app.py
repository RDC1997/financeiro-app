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

# garantir estado
if "page" not in st.session_state:
    st.session_state.page = "Casal"


# =========================
# NAVIGATION CARDS
# =========================
def nav_card(title, emoji, page_key):
    selected = st.session_state.page == page_key

    style = f"""
        border: 2px solid {'#4CAF50' if selected else '#ddd'};
        padding: 20px;
        border-radius: 12px;
        cursor: pointer;
        text-align: center;
        background-color: {'#f0fff4' if selected else 'white'};
    """

    if st.button(f"{emoji} {title}", key=page_key):
        st.session_state.page = page_key

    st.markdown(f"<div style='{style}'></div>", unsafe_allow_html=True)


# =========================
# HEADER NAVIGATION
# =========================
def render_menu():
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        nav_card("Casal", "👨‍❤️‍👩", "Casal")

    with col2:
        nav_card("Ruben", "🤴", "Ruben")

    with col3:
        nav_card("Gabi", "👸", "Gabi")

    with col4:
        nav_card("Metas", "🎯", "Metas")

    with col5:
        nav_card("Análises", "📊", "Analises")


# =========================
# LOAD DATA
# =========================
df = load_data()

if not df.empty:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")


# =========================
# CASAL
# =========================
def page_casal():
    st.title("👨‍❤️‍👩 Visão Geral do Casal")

    receitas = df[df["Tipo"].isin(["Salário", "Subsídio Alimentação"])]
    despesas = df[df["Tipo"] == "Despesa"]

    total_r = receitas["Valor"].sum()
    total_d = despesas["Valor"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Receitas", f"{total_r:.2f} €")
    col2.metric("Despesas", f"{total_d:.2f} €")
    col3.metric("Saldo", f"{total_r - total_d:.2f} €")

    st.divider()

    st.dataframe(df.tail(10), use_container_width=True)


# =========================
# ROD
# =========================
def page_person(name, emoji):
    st.title(f"{emoji} {name}")

    df_p = df[df["Pessoa"] == name]

    col1, col2, col3 = st.columns(3)

    receitas = df_p[df_p["Tipo"].isin(["Salário", "Subsídio Alimentação"])]
    despesas = df_p[df_p["Tipo"] == "Despesa"]

    col1.metric("Receitas", f"{receitas['Valor'].sum():.2f} €")
    col2.metric("Despesas", f"{despesas['Valor'].sum():.2f} €")
    col3.metric("Saldo", f"{receitas['Valor'].sum() - despesas['Valor'].sum():.2f} €")

    st.divider()

    st.dataframe(df_p.tail(10), use_container_width=True)


# =========================
# METAS
# =========================
def page_metas():
    st.title("🎯 Metas")

    st.info("Aqui podes integrar a tua lógica atual de metas")

    st.dataframe(df)


# =========================
# ANALISES
# =========================
def page_analises():
    st.title("📊 Análises")

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
# ROUTER
# =========================
render_menu()

st.divider()

if st.session_state.page == "Casal":
    page_casal()

elif st.session_state.page == "Ruben":
    page_person("Ruben", "🤴")

elif st.session_state.page == "Gabi":
    page_person("Gabi", "👸")

elif st.session_state.page == "Metas":
    page_metas()

elif st.session_state.page == "Analises":
    page_analises()
