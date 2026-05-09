import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from utils import (
    export_to_excel,
    refresh,
    validate_value,
    validate_category,
    generate_id
)

from data import (
    load_data,
    add_category,
    delete_category,
    aplicar_filtros,
    load_goals,
    add_goal,
    update_goal,
    delete_goal,
    sheet,
    SHEET_ID
)

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="Finance App", layout="wide")

if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None


# =========================
# SIDEBAR INFO
# =========================

def render_sidebar_info():
    with st.sidebar.expander("ℹ️ Info"):
        st.caption("Dados em cache por 1 minuto")
        st.markdown("**📄 ID da Planilha:**")
        st.code(SHEET_ID)


# =========================
# SIDEBAR CATEGORIES
# =========================

def render_sidebar_categories(categories, df):

    st.sidebar.markdown("## ⚙️ Categorias")

    with st.sidebar.expander("➕ Adicionar categoria"):
        new_cat = st.text_input("Nova categoria", key="new_cat_input")

        if st.button("Adicionar categoria", key="add_cat"):
            if new_cat.strip():
                add_category(new_cat.strip())
                refresh()

    with st.sidebar.expander("❌ Remover categoria"):
        if categories:
            cat_del = st.selectbox("Escolher", categories)
            if st.button("Remover categoria", key="del_cat"):
                delete_category(cat_del)
                refresh()

    with st.sidebar.expander("📋 Ver categorias"):
        if categories:
            contagem = df[df["Tipo"] == "Despesa"].groupby("Categoria").size()
            for cat in categories:
                st.write(f"• {cat}: {contagem.get(cat,0)}")


# =========================
# FILTERS (FIX DATETIME)
# =========================

def render_filters(df):

    meses = [
        "Todos","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
        "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
    ]

    df_temp = df.copy()

    df_temp["Data"] = pd.to_datetime(df_temp["Data"], errors="coerce")

    anos_disponiveis = sorted(
        df_temp["Data"].dropna().dt.year.unique().tolist(),
        reverse=True
    )

    filtro_ano = st.sidebar.selectbox("Ano", ["Todos"] + anos_disponiveis)
    filtro_mes = st.sidebar.selectbox("Mês", meses)
    pesquisa = st.sidebar.text_input("Pesquisar")

    return aplicar_filtros(df_temp, filtro_ano, filtro_mes, pesquisa, meses)


# =========================
# DELETE SECTION
# =========================

def render_delete_section(df_p):

    if df_p.empty:
        st.info("Sem registos")
        return

    for _, row in df_p.tail(10).iterrows():

        c1, c2, c3, c4, c5 = st.columns([2,2,2,2,1])

        c1.write(row["Tipo"])
        c2.write(row["Categoria"])
        c3.write(f"{row['Valor']} €")
        c4.write(row["Data"])

        if st.session_state.confirm_delete == row["ID"]:

            if c5.button("✓", key=f"c_{row['ID']}"):

                data = sheet.get_all_values()
                headers = data[0]
                idx = headers.index("ID")

                for i, r in enumerate(data[1:], start=2):
                    if r[idx] == row["ID"]:
                        sheet.delete_rows(i)
                        break

                st.session_state.confirm_delete = None
                load_data.clear()
                refresh()

        else:

            if c5.button("🗑️", key=f"d_{row['ID']}"):
                st.session_state.confirm_delete = row["ID"]
                refresh()


# =========================
# INDIVIDUAL MODE (FIXED UI LOGIC)
# =========================

def render_individual_mode(pessoa, categories, df):

    avatars = {"Ruben": "🤴", "Gabi": "👸"}
    st.subheader(f"{avatars.get(pessoa)} {pessoa}")

    # ---------------- INPUTS DINÂMICOS ----------------
    tipo = st.selectbox(
        "Tipo",
        ["Salário", "Subsídio Alimentação", "Despesa"]
    )

    categoria = None
    descricao = ""

    # IMPORTANTE: aparece imediatamente ao mudar "Despesa"
    if tipo == "Despesa":

        categoria = st.selectbox(
            "Categoria",
            categories + ["Outros"]
        )

        if categoria == "Outros":
            descricao = st.text_input("Descrição (obrigatória)")

    valor = st.number_input("Valor (€)", min_value=0.0)
    data = st.date_input("Data", datetime.today())

    # ---------------- SUBMIT ----------------
    if st.button("Adicionar"):

        erros = []

        erro_valor = validate_value(valor)
        if erro_valor:
            erros.append(erro_valor)

        if tipo == "Despesa":

            if not categoria:
                erros.append("Seleciona uma categoria")

            if categoria == "Outros" and not descricao.strip():
                erros.append("Descrição obrigatória para 'Outros'")

        if erros:
            for e in erros:
                st.error(e)
        else:

            sheet.append_row([
                generate_id(),
                pessoa,
                tipo,
                categoria,
                descricao,
                float(valor),
                str(data)
            ])

            load_data.clear()
            st.success("Registo adicionado")
            refresh()

    st.markdown("---")
    render_delete_section(df[df["Pessoa"] == pessoa])


# =========================
# CASAL MODE
# =========================

def render_casal_mode(df):

    st.subheader("Casal")

    receitas = df[df["Tipo"].isin(["Salário","Subsídio Alimentação"])]
    despesas = df[df["Tipo"] == "Despesa"]

    c1, c2, c3 = st.columns(3)

    c1.metric("Receitas", f"{receitas['Valor'].sum()} €")
    c2.metric("Despesas", f"{despesas['Valor'].sum()} €")
    c3.metric("Saldo", f"{receitas['Valor'].sum() - despesas['Valor'].sum()} €")

    st.markdown("---")

    for pessoa in ["Ruben", "Gabi"]:
        st.markdown(f"## {pessoa}")
        render_delete_section(df[df["Pessoa"] == pessoa])

    st.stop()


# =========================
# METAS
# =========================

def render_metas_mode():

    st.subheader("Metas")

    goals = load_goals()

    with st.expander("Criar meta"):
        nome = st.text_input("Nome")
        obj = st.number_input("Objetivo", min_value=0.0)

        if st.button("Criar"):
            if nome and obj > 0:
                add_goal(nome, obj)
                refresh()

    st.dataframe(goals)
    st.stop()


# =========================
# ANALISES
# =========================

def render_analises_mode(df):

    st.subheader("Análises")

    receitas = df[df["Tipo"].isin(["Salário","Subsídio Alimentação"])]
    despesas = df[df["Tipo"] == "Despesa"]

    st.metric("Receitas", receitas["Valor"].sum())
    st.metric("Despesas", despesas["Valor"].sum())

    st.stop()


# =========================
# MAIN
# =========================

st.title("Finance App")

df = load_data()
categorias = st.session_state.get("categories", [])

render_sidebar_info()
render_sidebar_categories(categorias, df)

modo = st.sidebar.radio("Modo", ["Ruben", "Gabi", "Casal", "Metas", "Análises"])

df_filtrado = render_filters(df)

if modo == "Ruben":
    render_individual_mode("Ruben", categorias, df_filtrado)

elif modo == "Gabi":
    render_individual_mode("Gabi", categorias, df_filtrado)

elif modo == "Casal":
    render_casal_mode(df_filtrado)

elif modo == "Metas":
    render_metas_mode()

elif modo == "Análises":
    render_analises_mode(df_filtrado)
