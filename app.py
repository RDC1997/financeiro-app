import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =========================
# FALLBACK EXPORT FUNCTION
# =========================
try:
    from utils import export_to_excel
except ImportError:
    from io import BytesIO

    def export_to_excel(df):
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')

        return output.getvalue()

from data import load_data

# =========================
# UI COMPONENTS
# =========================
def render_sidebar_categories(categories, df):
    st.sidebar.markdown("## ⚙️ Categorias")

    with st.sidebar.expander("➕ Adicionar categoria"):
        new_cat = st.text_input("Nova categoria", key="new_cat_input")
        if st.button("Adicionar categoria", key="add_cat"):
            if new_cat.strip():
                from data import add_category
                add_category(new_cat.strip())
                from utils import refresh
                refresh()

    with st.sidebar.expander("❌ Remover categoria"):
        if categories:
            cat_del = st.selectbox("Escolher", categories, key="cat_del_select")
            if st.button("Remover categoria", key="del_cat"):
                from data import delete_category
                delete_category(cat_del)
                from utils import refresh
                refresh()

    with st.sidebar.expander("📋 Ver categorias"):
        if categories:
            contagem = df[df["Tipo"] == "Despesa"].groupby('Categoria').size()
            for cat in categories:
                qtd = contagem.get(cat, 0)
                st.write(f"• {cat}: {qtd} registos")
        else:
            st.write("Sem categorias")

def render_filters(df):
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔍 Filtros")

    try:
        anos_disponiveis = sorted(df["Data"].dt.year.unique().tolist(), reverse=True) if not df.empty and "Data" in df.columns else [datetime.now().year]
    except:
        anos_disponiveis = [datetime.now().year]

    meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    filtro_ano = st.sidebar.selectbox("Ano", ["Todos"] + anos_disponiveis, key="filtro_ano", index=0)
    filtro_mes = st.sidebar.selectbox("Mês", meses, key="filtro_mes", index=0)
    pesquisa = st.sidebar.text_input("🔎 Pesquisar", key="pesquisa", value="")

    from data import aplicar_filtros
    df_filtrado = aplicar_filtros(df, filtro_ano, filtro_mes, pesquisa, meses)
    return df_filtrado

def render_casal_mode(df_filtrado):
    st.subheader("👨‍❤️‍👩 Casal - PRO 2 Inteligente")

    def get_last_salary(df, pessoa):
        df_p = df[(df["Pessoa"] == pessoa) & (df["Tipo"] == "Salário")]
        if df_p.empty:
            return None
        return df_p.sort_values("Data", ascending=False).iloc[0]["Data"]

    def filtrar_ciclo(df, pessoa):
        last_salary = get_last_salary(df, pessoa)
        if last_salary:
            return df[(df["Pessoa"] == pessoa) & (df["Data"] >= last_salary)]
        return df[df["Pessoa"] == pessoa]

    df_casal = df_filtrado.copy()
    receitas_casal = df_casal[df_casal["Tipo"].isin(["Salário","Subsídio Alimentação"])]
    despesas_casal = df_casal[df_casal["Tipo"] == "Despesa"]
    
    total_receitas_casal = receitas_casal["Valor"].sum()
    total_despesas_casal = despesas_casal["Valor"].sum()
    saldo_casal = total_receitas_casal - total_despesas_casal
    
    st.markdown("### 💑 Totais do Casal")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Receitas", f"{total_receitas_casal:.2f} €")
    c2.metric("💸 Despesas", f"{total_despesas_casal:.2f} €")
    c3.metric("📊 Saldo", f"{saldo_casal:.2f} €", delta_color="normal")

    st.markdown("---")

    avatars = {"Ruben":"🤴","Gabi":"👸"}
    for pessoa in ["Ruben", "Gabi"]:
        st.markdown(f"### {avatars[pessoa]} {pessoa}")
        
        last_salary_date = get_last_salary(df_filtrado, pessoa)
        if last_salary_date:
            st.caption(f"📅 Ciclo desde: {last_salary_date.strftime('%d-%m-%Y')}")
        else:
            st.caption("📅 Sem registo de salário")

        df_p = filtrar_ciclo(df_filtrado, pessoa)
        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        total_receitas = receitas["Valor"].sum()
        total_despesas = despesas["Valor"].sum()
        saldo = total_receitas - total_despesas

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Receitas", f"{total_receitas:.2f} €")
        c2.metric("💸 Despesas", f"{total_despesas:.2f} €")
        c3.metric("📊 Saldo", f"{saldo:.2f} €")

        with st.expander("💰 Receitas"):
            if not receitas.empty:
                df_show = receitas.drop(columns=["ID"])
                if 'Data' in df_show.columns:
                    df_show['Data'] = pd.to_datetime(df_show['Data']).dt.strftime('%d-%m-%Y')
                st.dataframe(df_show, use_container_width=True)
            else:
                st.info("Sem receitas neste ciclo")

        with st.expander("💸 Despesas"):
            if not despesas.empty:
                df_show = despesas.drop(columns=["ID"])
                if 'Data' in df_show.columns:
                    df_show['Data'] = pd.to_datetime(df_show['Data']).dt.strftime('%d-%m-%Y')
                st.dataframe(df_show, use_container_width=True)
            else:
                st.info("Sem despesas neste ciclo")

        render_delete_section(df_p)

        st.markdown("---")

    st.stop()

def render_metas_mode():
    st.subheader("🎯 Metas")

    from data import load_goals, add_goal, update_goal, delete_goal
    goals = load_goals()

    with st.expander("➕ Criar meta"):
        nome = st.text_input("Nome da meta", key="meta_nome")
        obj = st.number_input("Objetivo (€)", min_value=0.0, key="meta_obj")
        if st.button("Criar meta", key="criar_meta"):
            if nome.strip() and obj > 0:
                add_goal(nome, obj)
                from utils import refresh
                refresh()
            else:
                st.error("Preencha o nome e um objetivo maior que 0")

    if goals.empty:
        st.info("Ainda não existem metas criadas.")
    else:
        st.dataframe(goals, use_container_width=True)
        
        st.markdown("### 📈 Progresso das Metas")
        
        if not goals.empty:
            goals_plot = goals.copy()
            goals_plot['Progresso'] = goals_plot.apply(
                lambda x: min((float(x.get('Atual', 0)) / float(x.get('Objetivo', 1)) * 100), 100) 
                if float(x.get('Objetivo', 0)) > 0 else 0, 
                axis=1
            )
            fig_bar = px.bar(
                goals_plot, 
                x='Meta', 
                y='Progresso',
                title="Progresso das Metas (%)",
                color='Progresso',
                color_continuous_scale='Greens',
                range_y=[0, 100]
            )
            st.plotly_chart(fig_bar, use_container_width=True)
