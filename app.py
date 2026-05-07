import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils import export_to_excel
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
        
        for _, goal in goals.iterrows():
            objetivo = float(goal.get('Objetivo', 0))
            atual = float(goal.get('Atual', 0))
            progresso = min((atual / objetivo * 100), 100) if objetivo > 0 else 0
            st.progress(int(progresso), text=f"{goal['Meta']}: {progresso:.1f}% ({atual:.2f}€ / {objetivo:.2f}€)")
        
        st.markdown("---")
        st.markdown("### 💵 Atualizar Meta")
        
        col1, col2 = st.columns(2)
        with col1:
            meta_selecionada = st.selectbox("Selecionar meta", goals['Meta'].tolist())
        with col2:
            valor_adicionar = st.number_input("Valor a adicionar (€)", min_value=0.0, key="atualizar_meta")
        
        if st.button("Atualizar", key="atualizar_meta_btn"):
            if meta_selecionada and valor_adicionar > 0:
                update_goal(meta_selecionada, valor_adicionar)
                from utils import refresh
                refresh()
            else:
                st.error("Selecione uma meta e adicione um valor")
        
        st.markdown("---")
        st.markdown("### 🗑 Eliminar Meta")
        
        col1, col2 = st.columns(2)
        with col1:
            meta_eliminar = st.selectbox("Selecionar meta para eliminar", goals['Meta'].tolist(), key="meta_del_select")
        with col2:
            st.write("")
        
        if st.button("Eliminar Meta", key="del_meta_btn"):
            if meta_eliminar:
                delete_goal(meta_eliminar)
                st.success("✅ Meta eliminada!")
                import time
                time.sleep(1)
                from utils import refresh
                refresh()
            else:
                st.error("Selecione uma meta para eliminar")

    st.stop()

def render_analises_mode(df_filtrado):
    st.subheader("📊 Resumo Financeiro")

    df_analise = df_filtrado.copy()
    
    if df_analise.empty:
        st.info("Sem dados para analisar")
        st.stop()

    if 'Data' not in df_analise.columns or df_analise['Data'].isna().all():
        st.warning("⚠️ Sem dados de data válidos para análises")
        st.stop()
    
    try:
        df_analise['Data'] = pd.to_datetime(df_analise['Data'], errors='coerce').dt.date
    except:
        st.warning("⚠️ Erro ao processar datas")
        st.stop()

    receitas = df_analise[df_analise["Tipo"].isin(["Salário","Subsídio Alimentação"])]
    despesas = df_analise[df_analise["Tipo"] == "Despesa"]

    st.markdown("### 💰 Resumo do Período")
    
    col1, col2, col3 = st.columns(3)
    
    total_receitas = receitas['Valor'].sum()
    total_despesas = despesas['Valor'].sum()
    saldo = total_receitas - total_despesas
    
    col1.metric("Total Receitas", f"{total_receitas:,.2f} €")
    col2.metric("Total Despesas", f"{total_despesas:,.2f} €")
    col3.metric("Saldo", f"{saldo:,.2f} €", 
                delta=f"{saldo:,.2f} €" if saldo >= 0 else f"{saldo:,.2f} €",
                delta_color="normal" if saldo >= 0 else "inverse")

    st.markdown("---")

    if not despesas.empty:
        st.markdown("### 🍰 Onde gastaste o dinheiro?")
        
        despesa_categoria = despesas.groupby('Categoria')['Valor'].sum().sort_values(ascending=False)
        
        fig_pie = px.pie(
            values=despesa_categoria.values, 
            names=despesa_categoria.index,
            title="Despesas por Categoria",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("**Detalhe:**")
        for cat, valor in despesa_categoria.items():
            pct = (valor / total_despesas * 100) if total_despesas > 0 else 0
            st.write(f"• **{cat}**: {valor:,.2f} € ({pct:.1f}%)")

    st.markdown("---")

    st.markdown("### 📋 Últimos Registos")
    
    ultimos = df_analise.head(10)
    
    if not ultimos.empty:
        cols_show = ['Pessoa', 'Tipo', 'Categoria', 'Valor', 'Data']
        cols_exist = [c for c in cols_show if c in ultimos.columns]
        df_view = ultimos[cols_exist].copy()
        if 'Data' in df_view.columns:
            df_view['Data'] = pd.to_datetime(df_view['Data']).dt.strftime('%d-%m-%Y')
        
        styled_df = df_view.style.apply(
            lambda x: ['color: red; font-weight: bold' if isinstance(v, (int, float)) and v > 200 else '' for v in x], 
            subset=['Valor']
        )
        
        st.dataframe(styled_df, use_container_width=True)

    st.markdown("---")

    st.markdown("### 📥 Exportar Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df_analise.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descarregar CSV",
            data=csv,
            file_name="finance_app_export.csv",
            mime="text/csv",
            key="export_csv"
        )
    
    with col2:
        excel_data = export_to_excel(df_analise)
        st.download_button(
            label="📊 Descarregar Excel",
            data=excel_data,
            file_name="finance_app_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="export_excel"
        )
    
    st.info("💡 Os ficheiros exportados contêm apenas os dados filtrados atualmente.")

    st.stop()

def render_individual_mode(pessoa, categories, df):
    avatars = {"Ruben":"🤴","Gabi":"👸"}
    st.subheader(f"{avatars.get(pessoa,'👤')} {pessoa}")

    with st.form("adicionar_registo", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"], key="tipo_select")
        
        categoria = ""
        descricao = ""
        
        if tipo == "Despesa":
            todas_categorias = categories + ["Outros"] if categories else ["Outros"]
            categoria = st.selectbox("Categoria", todas_categorias, key="cat_select")
            if categoria == "Outros":
                descricao = st.text_input("Descrição (especifique)", key="desc_input")
        
        valor = st.number_input("Valor (€)", min_value=0.0, key="valor_input")
        data = st.date_input("Data", datetime.today(), max_value=datetime.today().date(), key="data_input")
        
        submitted = st.form_submit_button("✅ Adicionar", use_container_width=True)

    if submitted:
        from utils import validate_value, validate_category
        erros = []
        
        erro_valor = validate_value(valor)
        if erro_valor:
            erros.append(erro_valor)
        
        erro_cat = validate_category(tipo, categoria, descricao)
        if erro_cat:
            erros.append(erro_cat)
        
        if erros:
            for erro in erros:
                st.error(erro)
        else:
            from data import sheet
            from utils import generate_id
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
            st.toast("✅ Registado com sucesso!", icon="💰")
            import time
            time.sleep(1)
            from utils import refresh
            refresh()

    st.markdown("---")
    st.markdown("### 🗑 Eliminar Registos")

    df_pessoa = df[df["Pessoa"] == pessoa]

    if df_pessoa.empty:
        st.info(f"Sem registos para {pessoa}")
    else:
        st.warning("⚠️ Clique no botão para eliminar um registo")
        
        df_pessoa_limited = df_pessoa.tail(10)
        
        for idx, (_, row) in enumerate(df_pessoa_limited.iterrows()):
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])
                
                c1.write(row["Tipo"])
                c2.write(row["Categoria"])
                c3.write(row["Descrição"] if pd.notna(row["Descrição"]) else "")
                c4.write(f"{row['Valor']:.2f} €")
                
                if st.session_state.confirm_delete == row["ID"]:
                    c5.write("❓")
                    col_confirm, col_cancel = st.columns(2)
                    if col_confirm.button("✓", key=f"confirm_{row['ID']}"):
                        from data import sheet
                        data = sheet.get_all_values()
                        headers = data[0]
                        id_index = headers.index("ID")
                        
                        for i, r in enumerate(data[1:], start=2):
                            if r[id_index] == row["ID"]:
                                sheet.delete_rows(i)
                                break
                        
                        st.session_state.confirm_delete = None
                        load_data.clear()
                        from utils import refresh
                        refresh()
                    
                    if col_cancel.button("✗", key=f"cancel_{row['ID']}"):
                        st.session_state.confirm_delete = None
                        from utils import refresh
                        refresh()
                else:
                    if c5.button("🗑️", key=f"del_{row['ID']}"):
                        st.session_state.confirm_delete = row["ID"]
                        from utils import refresh
                        refresh()
                
                st.divider()

def render_delete_section(df_p):
    if not df_p.empty:
        st.warning("⚠️ Clique no botão para eliminar um registo")
        
        df_p_limited = df_p.tail(10)
        
        for idx, (_, row) in enumerate(df_p_limited.iterrows()):
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])
                
                c1.write(row["Pessoa"])
                c2.write(row["Tipo"])
                c3.write(row["Categoria"])
                c4.write(f"{row['Valor']:.2f} €")
                
                if st.session_state.confirm_delete == row["ID"]:
                    c5.write("❓")
                    col_confirm, col_cancel = st.columns(2)
                    if col_confirm.button("✓", key=f"confirm_{row['ID']}"):
                        from data import sheet
                        data = sheet.get_all_values()
                        headers = data[0]
                        id_index = headers.index("ID")
                        
                        for i, r in enumerate(data[1:], start=2):
                            if r[id_index] == row["ID"]:
                                sheet.delete_rows(i)
                                break
                        
                        st.session_state.confirm_delete = None
                        load_data.clear()
                        from utils import refresh
                        refresh()
                    
                    if col_cancel.button("✗", key=f"cancel_{row['ID']}"):
                        st.session_state.confirm_delete = None
                        from utils import refresh
                        refresh()
                else:
                    if c5.button("🗑️", key=f"del_{row['ID']}"):
                        st.session_state.confirm_delete = row["ID"]
                        from utils import refresh
                        refresh()
                
                st.divider()
    else:
        st.info("Sem registos para eliminar")

def render_sidebar_info():
    with st.sidebar.expander("ℹ️ Info"):
        st.caption("Dados em cache por 1 minuto para evitar exceder limites da API Google")

        try:
            service_account_email = st.secrets["google_service_account"]["client_email"]
            st.markdown("**📧 Conta de serviço:**")
            st.code(service_account_email, language=None)
            st.caption("Copie este e-mail e partilhe a planilha do Google Sheets com ele (permissão de editor).")
        except Exception:
            st.caption("E-mail da conta de serviço não disponível.")

        from data import SHEET_ID
        st.markdown("**📄 ID da Planilha:**")
        st.code(SHEET_ID, language=None)
        st.caption("Verifique se este ID corresponde à sua planilha do Google Sheets.")

        st.markdown("**🔧 Diagnóstico:**")
        st.markdown("""
        1. Abra a planilha no Google Sheets
        2. Clique em "Compartilhar"
        3. Cole o e-mail acima e dê permissão de "Editor"
        4. Verifique se o ID da planilha está correto
        """)
