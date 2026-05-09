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

st.set_page_config(
    page_title="Finance App",
    layout="wide"
)

if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

# =========================
# SIDEBAR CATEGORIES
# =========================

def render_sidebar_categories(categories, df):

    st.sidebar.markdown("## ⚙️ Categorias")

    with st.sidebar.expander("➕ Adicionar categoria"):

        new_cat = st.text_input(
            "Nova categoria",
            key="new_cat_input"
        )

        if st.button("Adicionar categoria", key="add_cat"):

            if new_cat.strip():

                add_category(new_cat.strip())
                refresh()

    with st.sidebar.expander("❌ Remover categoria"):

        if categories:

            cat_del = st.selectbox(
                "Escolher",
                categories,
                key="cat_del_select"
            )

            if st.button(
                "Remover categoria",
                key="del_cat"
            ):

                delete_category(cat_del)
                refresh()

    with st.sidebar.expander("📋 Ver categorias"):

        if categories:

            contagem = (
                df[df["Tipo"] == "Despesa"]
                .groupby("Categoria")
                .size()
            )

            for cat in categories:

                qtd = contagem.get(cat, 0)
                st.write(f"• {cat}: {qtd} registos")

        else:
            st.write("Sem categorias")


# =========================
# FILTERS
# =========================

def render_filters(df):

    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔍 Filtros")

    try:

        anos_disponiveis = sorted(
            df["Data"].dt.year.unique().tolist(),
            reverse=True
        )

    except:
        anos_disponiveis = [datetime.now().year]

    meses = [
        "Todos",
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro"
    ]

    filtro_ano = st.sidebar.selectbox(
        "Ano",
        ["Todos"] + anos_disponiveis
    )

    filtro_mes = st.sidebar.selectbox(
        "Mês",
        meses
    )

    pesquisa = st.sidebar.text_input(
        "🔎 Pesquisar"
    )

    return aplicar_filtros(
        df,
        filtro_ano,
        filtro_mes,
        pesquisa,
        meses
    )


# =========================
# DELETE SECTION
# =========================

def render_delete_section(df_p):

    if df_p.empty:
        st.info("Sem registos")
        return

    st.markdown("### 🗑 Eliminar Registos")

    df_p_limited = df_p.tail(10)

    for _, row in df_p_limited.iterrows():

        with st.container():

            c1, c2, c3, c4, c5 = st.columns([2,2,2,2,1])

            c1.write(row["Tipo"])
            c2.write(row["Categoria"])
            c3.write(f"{row['Valor']:.2f} €")
            c4.write(str(row["Data"]))

            if st.session_state.confirm_delete == row["ID"]:

                if c5.button("✓", key=f"confirm_{row['ID']}"):

                    data = sheet.get_all_values()
                    headers = data[0]

                    id_index = headers.index("ID")

                    for i, r in enumerate(data[1:], start=2):

                        if r[id_index] == row["ID"]:
                            sheet.delete_rows(i)
                            break

                    st.session_state.confirm_delete = None

                    load_data.clear()
                    refresh()

            else:

                if c5.button("🗑️", key=f"del_{row['ID']}"):

                    st.session_state.confirm_delete = row["ID"]
                    refresh()

            st.divider()


# =========================
# INDIVIDUAL MODE
# =========================

def render_individual_mode(
    pessoa,
    categories,
    df
):

    avatars = {
        "Ruben": "🤴",
        "Gabi": "👸"
    }

    st.subheader(
        f"{avatars.get(pessoa,'👤')} {pessoa}"
    )

    with st.form(
        "adicionar_registo",
        clear_on_submit=True
    ):

        tipo = st.selectbox(
            "Tipo",
            [
                "Salário",
                "Subsídio Alimentação",
                "Despesa"
            ]
        )

        categoria = ""
        descricao = ""

        if tipo == "Despesa":

            todas_categorias = (
                categories + ["Outros"]
            )

            categoria = st.selectbox(
                "Categoria",
                todas_categorias
            )

            if categoria == "Outros":

                descricao = st.text_input(
                    "Descrição"
                )

        valor = st.number_input(
            "Valor (€)",
            min_value=0.0
        )

        data = st.date_input(
            "Data",
            datetime.today()
        )

        submitted = st.form_submit_button(
            "✅ Adicionar"
        )

    if submitted:

        erros = []

        erro_valor = validate_value(valor)

        if erro_valor:
            erros.append(erro_valor)

        erro_cat = validate_category(
            tipo,
            categoria,
            descricao
        )

        if erro_cat:
            erros.append(erro_cat)

        if erros:

            for erro in erros:
                st.error(erro)

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

            st.success("✅ Registo criado")

            refresh()

    st.markdown("---")

    df_pessoa = df[df["Pessoa"] == pessoa]

    render_delete_section(df_pessoa)


# =========================
# CASAL MODE
# =========================

def render_casal_mode(df_filtrado):

    st.subheader("👨‍❤️‍👩 Casal")

    receitas = df_filtrado[
        df_filtrado["Tipo"].isin([
            "Salário",
            "Subsídio Alimentação"
        ])
    ]

    despesas = df_filtrado[
        df_filtrado["Tipo"] == "Despesa"
    ]

    total_receitas = receitas["Valor"].sum()
    total_despesas = despesas["Valor"].sum()

    saldo = total_receitas - total_despesas

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "💰 Receitas",
        f"{total_receitas:.2f} €"
    )

    c2.metric(
        "💸 Despesas",
        f"{total_despesas:.2f} €"
    )

    c3.metric(
        "📊 Saldo",
        f"{saldo:.2f} €"
    )

    st.markdown("---")

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {pessoa}")

        df_p = df_filtrado[
            df_filtrado["Pessoa"] == pessoa
        ]

        st.dataframe(
            df_p,
            use_container_width=True
        )

        render_delete_section(df_p)

    st.stop()


# =========================
# METAS
# =========================

def render_metas_mode():

    st.subheader("🎯 Metas")

    goals = load_goals()

    with st.expander("➕ Criar meta"):

        nome = st.text_input("Nome")

        objetivo = st.number_input(
            "Objetivo (€)",
            min_value=0.0
        )

        if st.button("Criar"):

            if nome.strip() and objetivo > 0:

                add_goal(nome, objetivo)
                refresh()

    if goals.empty:

        st.info("Sem metas")

    else:

        st.dataframe(
            goals,
            use_container_width=True
        )

        for _, goal in goals.iterrows():

            objetivo = float(goal["Objetivo"])
            atual = float(goal["Atual"])

            progresso = (
                atual / objetivo
            ) * 100 if objetivo > 0 else 0

            st.progress(
                int(min(progresso,100)),
                text=f"{goal['Meta']} "
                f"({progresso:.1f}%)"
            )

    st.stop()


# =========================
# ANALISES
# =========================

def render_analises_mode(df):

    st.subheader("📊 Resumo Financeiro")

    if df.empty:

        st.info("Sem dados")
        st.stop()

    receitas = df[
        df["Tipo"].isin([
            "Salário",
            "Subsídio Alimentação"
        ])
    ]

    despesas = df[
        df["Tipo"] == "Despesa"
    ]

    total_receitas = receitas["Valor"].sum()
    total_despesas = despesas["Valor"].sum()

    saldo = total_receitas - total_despesas

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Receitas",
        f"{total_receitas:.2f} €"
    )

    c2.metric(
        "Despesas",
        f"{total_despesas:.2f} €"
    )

    c3.metric(
        "Saldo",
        f"{saldo:.2f} €"
    )

    st.markdown("---")

    if not despesas.empty:

        despesa_categoria = (
            despesas.groupby("Categoria")["Valor"]
            .sum()
            .sort_values(ascending=False)
        )

        fig = px.pie(
            values=despesa_categoria.values,
            names=despesa_categoria.index,
            title="Despesas por Categoria"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("---")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📄 Exportar CSV",
        csv,
        "finance.csv",
        "text/csv"
    )

    excel_data = export_to_excel(df)

    st.download_button(
        "📊 Exportar Excel",
        excel_data,
        "finance.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.stop()


# =========================
# SIDEBAR INFO
# =========================

def render_sidebar_info():

    with st.sidebar.expander("ℹ️ Info"):

        st.caption(
            "Dados em cache por 1 minuto"
        )

        st.markdown("**📄 ID da Planilha:**")
        st.code(SHEET_ID)

        st.markdown(
            """
            1. Abra a planilha
            2. Compartilhe
            3. Dê acesso de editor
            """
        )


# =========================
# MAIN
# =========================

st.title("💰 Finance App")

df = load_data()

categorias = st.session_state.categories

render_sidebar_info()

render_sidebar_categories(
    categorias,
    df
)

modo = st.sidebar.radio(
    "Modo",
    [
        "Ruben",
        "Gabi",
        "Casal",
        "Metas",
        "Análises"
    ]
)

df_filtrado = render_filters(df)

if modo == "Ruben":

    render_individual_mode(
        "Ruben",
        categorias,
        df_filtrado
    )

elif modo == "Gabi":

    render_individual_mode(
        "Gabi",
        categorias,
        df_filtrado
    )

elif modo == "Casal":

    render_casal_mode(df_filtrado)

elif modo == "Metas":

    render_metas_mode()

elif modo == "Análises":

    render_analises_mode(df_filtrado)
