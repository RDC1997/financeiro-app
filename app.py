import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
import time
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(
    page_title="Rubi&Gabi", 
    layout="wide",
    page_icon="💰"
)
st.title("💰 Controlo Financeiro PRO")

# =========================
# SESSION STATE
# =========================
if 'inputs' not in st.session_state:
    st.session_state.inputs = {
        'valor': 0.0,
        'descricao': '',
        'categoria': ''
    }

if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = None

if 'filtros' not in st.session_state:
    st.session_state.filtros = {
        'mes': None,
        'ano': None,
        'pesquisa': ''
    }

# =========================
# HELPERS
# =========================
def refresh():
    st.cache_data.clear()
    # Limpar cache específico
    load_data.clear()
    load_categories.clear()
    try:
        load_goals.clear()
    except:
        pass
    st.rerun()

def generate_id():
    return str(uuid.uuid4())

def reset_inputs():
    st.session_state.inputs = {
        'valor': 0.0,
        'descricao': '',
        'categoria': ''
    }

def export_to_excel(df):
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
        return output.getvalue()
    except Exception as e:
        # Fallback: retornar CSV se Excel falhar
        return df.to_csv(index=False).encode('utf-8')

# Contador de chamadas API (para debug)
if 'api_calls' not in st.session_state:
    st.session_state.api_calls = 0

# =========================
# GOOGLE SHEETS
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    SHEET_ID = "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"

    sheet = client.open_by_key(SHEET_ID).sheet1
    cat_sheet = client.open_by_key(SHEET_ID).worksheet("Categorias")

    try:
        goal_sheet = client.open_by_key(SHEET_ID).worksheet("Metas")
    except:
        goal_sheet = client.open_by_key(SHEET_ID).add_worksheet("Metas", 100, 3)
        goal_sheet.append_row(["Meta","Objetivo","Atual"])

except Exception as e:
    st.error(f"Erro Google Sheets: {e}")
    st.stop()

# =========================
# CATEGORIAS
# =========================
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_categories():
    data = cat_sheet.get_all_values()
    return [row[0] for row in data[1:] if row[0].strip() != ""]

def add_category(cat):
    cat_sheet.append_row([cat])
    # Limpar cache após adicionar
    load_categories.clear()

def delete_category(cat):
    data = cat_sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == cat:
            cat_sheet.delete_rows(i + 1)
            break
    # Limpar cache após eliminar
    load_categories.clear()

categories = load_categories()

# =========================
# DATA
# =========================
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    raw = sheet.get_all_values()
    cols = ["ID","Pessoa","Tipo","Categoria","Descrição","Valor","Data"]

    if len(raw) < 2:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(raw[1:], columns=raw[0])

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    # Converter Data e manter apenas a parte da data (sem hora)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date

    return df

df = load_data()

# =========================
# MENU
# =========================
modo = st.sidebar.selectbox(
    "Modo",
    ["Casal 👨‍❤️‍👩","Ruben 🤴","Gabi 👸","Metas 🎯","Análises 📊"]
)

avatars = {"Ruben":"🤴","Gabi":"👸"}

# =========================
# CATEGORIAS UI
# =========================
st.sidebar.markdown("## ⚙️ Categorias")

with st.sidebar.expander("➕ Adicionar categoria"):
    new_cat = st.text_input("Nova categoria", key="new_cat_input")

    if st.button("Adicionar categoria", key="add_cat"):
        if new_cat.strip():
            add_category(new_cat.strip())
            refresh()

with st.sidebar.expander("❌ Remover categoria"):
    if categories:
        cat_del = st.selectbox("Escolher", categories, key="cat_del_select")

        if st.button("Remover categoria", key="del_cat"):
            delete_category(cat_del)
            refresh()

with st.sidebar.expander("📋 Ver categorias"):
    if categories:
        # Contagem de registos por categoria
        contagem = df[df["Tipo"] == "Despesa"].groupby('Categoria').size()
        for cat in categories:
            qtd = contagem.get(cat, 0)
            st.write(f"• {cat}: {qtd} registos")
    else:
        st.write("Sem categorias")

# =========================
# FILTROS
# =========================
st.sidebar.markdown("---")
st.sidebar.markdown("## 🔍 Filtros")

# Verificar se há dados válidos
try:
    anos_disponiveis = sorted(df["Data"].dt.year.unique().tolist(), reverse=True) if not df.empty and "Data" in df.columns else [datetime.now().year]
except:
    anos_disponiveis = [datetime.now().year]

meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

filtro_ano = st.sidebar.selectbox("Ano", ["Todos"] + anos_disponiveis, key="filtro_ano")
filtro_mes = st.sidebar.selectbox("Mês", meses, key="filtro_mes")
pesquisa = st.sidebar.text_input("🔎 Pesquisar", key="pesquisa")

def aplicar_filtros(df, ano, mes, pesquisa):
    df_f = df.copy()
    
    if ano != "Todos":
        df_f = df_f[df_f["Data"].dt.year == int(ano)]
    
    if mes != "Todos":
        mes_idx = meses.index(mes)
        df_f = df_f[df_f["Data"].dt.month == mes_idx]
    
    if pesquisa:
        df_f = df_f[df_f["Descrição"].str.contains(pesquisa, case=False, na=False)]
    
    return df_f

df_filtrado = aplicar_filtros(df, filtro_ano, filtro_mes, pesquisa)

# =========================
# CASAL
# =========================
if modo == "Casal 👨‍❤️‍👩":

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

    # Totais do casal
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

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"### {avatars[pessoa]} {pessoa}")

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
                cols_to_show = [c for c in ["ID"] if c in receitas.columns]
                df_show = receitas.drop(columns=cols_to_show)
                # Formatar data para mostrar apenas dia/mês/ano
                if 'Data' in df_show.columns:
                    df_show['Data'] = pd.to_datetime(df_show['Data']).dt.strftime('%d-%m-%Y')
                st.dataframe(
                    df_show,
                    use_container_width=True
                )
            else:
                st.info("Sem receitas neste ciclo")

        with st.expander("💸 Despesas"):
            if not despesas.empty:
                # Mostrar também a descrição se existir
                cols_to_show = [c for c in ["ID"] if c in despesas.columns]
                df_show = despesas.drop(columns=cols_to_show)
                # Formatar data para mostrar apenas dia/mês/ano
                if 'Data' in df_show.columns:
                    df_show['Data'] = pd.to_datetime(df_show['Data']).dt.strftime('%d-%m-%Y')
                st.dataframe(
                    df_show,
                    use_container_width=True
                )
            else:
                st.info("Sem despesas neste ciclo")

        with st.expander("🗑 Eliminar registos"):
            if not df_p.empty:
                st.warning("⚠️ Clique no botão para eliminar um registo")
                
                # Mostrar apenas últimos 10 registos para evitar muitas linhas
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
                                data = sheet.get_all_values()
                                headers = data[0]
                                id_index = headers.index("ID")
                                
                                for i, r in enumerate(data[1:], start=2):
                                    if r[id_index] == row["ID"]:
                                        sheet.delete_rows(i)
                                        break
                                
                                st.session_state.confirm_delete = None
                                load_data.clear()  # Limpar cache
                                refresh()
                            
                            if col_cancel.button("✗", key=f"cancel_{row['ID']}"):
                                st.session_state.confirm_delete = None
                                refresh()
                        else:
                            if c5.button("🗑️", key=f"del_{row['ID']}"):
                                st.session_state.confirm_delete = row["ID"]
                                refresh()
                        
                        st.divider()
            else:
                st.info("Sem registos para eliminar")

        st.markdown("---")

    st.stop()

# =========================
# METAS
# =========================
if modo == "Metas 🎯":

    st.subheader("🎯 Metas")

    @st.cache_data(ttl=300)
    def load_goals():
        raw = goal_sheet.get_all_values()
        return pd.DataFrame(raw[1:], columns=raw[0]) if len(raw) > 1 else pd.DataFrame()

    goals = load_goals()

    with st.expander("➕ Criar meta"):
        nome = st.text_input("Nome da meta", key="meta_nome")
        obj = st.number_input("Objetivo (€)", min_value=0.0, key="meta_obj")

        if st.button("Criar meta", key="criar_meta"):
            if nome.strip() and obj > 0:
                goal_sheet.append_row([nome.strip(), obj, 0])
                refresh()
            else:
                st.error("Preencha o nome e um objetivo maior que 0")

    if goals.empty:
        st.info("Ainda não existem metas criadas.")
    else:
        st.dataframe(goals, use_container_width=True)
        
        st.markdown("### 📈 Progresso das Metas")
        
        for _, goal in goals.iterrows():
            objetivo = float(goal.get('Objetivo', 0))
            atual = float(goal.get('Atual', 0))
            progresso = min((atual / objetivo * 100), 100) if objetivo > 0 else 0
            
            st.progress(int(progresso), text=f"{goal['Meta']}: {progresso:.1f}% ({atual:.2f}€ / {objetivo:.2f}€)")
        
        # Atualizar meta
        st.markdown("---")
        st.markdown("### 💵 Atualizar Meta")
        
        col1, col2 = st.columns(2)
        with col1:
            meta_selecionada = st.selectbox("Selecionar meta", goals['Meta'].tolist() if not goals.empty else [])
        with col2:
            valor_adicionar = st.number_input("Valor a adicionar (€)", min_value=0.0, key="atualizar_meta")
        
        if st.button("Atualizar", key="atualizar_meta_btn"):
            if meta_selecionada and valor_adicionar > 0:
                data = goal_sheet.get_all_values()
                for i, row in enumerate(data):
                    if i == 0:
                        continue
                    if row[0] == meta_selecionada:
                        atual = float(row[2]) if row[2] else 0
                        goal_sheet.update_cell(i + 1, 3, atual + valor_adicionar)
                        refresh()
            else:
                st.error("Selecione uma meta e adicione um valor")
        
        # Eliminar meta
        st.markdown("---")
        st.markdown("### 🗑 Eliminar Meta")
        
        col1, col2 = st.columns(2)
        with col1:
            meta_eliminar = st.selectbox("Selecionar meta para eliminar", goals['Meta'].tolist() if not goals.empty else [], key="meta_del_select")
        with col2:
            st.write("")  # Espaço vazio
        
        if st.button("Eliminar Meta", key="del_meta_btn"):
            if meta_eliminar:
                data = goal_sheet.get_all_values()
                for i, row in enumerate(data):
                    if i == 0:
                        continue
                    if row[0] == meta_eliminar:
                        goal_sheet.delete_rows(i + 1)
                        st.success("✅ Meta eliminada!")
                        time.sleep(1)
                        refresh()
            else:
                st.error("Selecione uma meta para eliminar")

    st.stop()

# =========================
# ANÁLISES
# =========================
if modo == "Análises 📊":

    st.subheader("📊 Resumo Financeiro")

    df_analise = df_filtrado.copy()
    
    if df_analise.empty:
        st.info("Sem dados para analisar")
        st.stop()

    # Verificar se a coluna Data existe e é válida
    if 'Data' not in df_analise.columns or df_analise['Data'].isna().all():
        st.warning("⚠️ Sem dados de data válidos para análises")
        st.stop()
    
    # Converter Data para datetime se necessário
    try:
        df_analise['Data'] = pd.to_datetime(df_analise['Data'], errors='coerce').dt.date
    except:
        st.warning("⚠️ Erro ao processar datas")
        st.stop()

    # Separar receitas e despesas
    receitas = df_analise[df_analise["Tipo"].isin(["Salário","Subsídio Alimentação"])]
    despesas = df_analise[df_analise["Tipo"] == "Despesa"]

    # === RESUMO GERAL ===
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

    # === DESPESAS POR CATEGORIA ===
    if not despesas.empty:
        st.markdown("### 🍰 Onde gastaste o dinheiro?")
        
        despesa_categoria = despesas.groupby('Categoria')['Valor'].sum().sort_values(ascending=False)
        
        # Mostrar como lista simples
        for cat, valor in despesa_categoria.items():
            pct = (valor / total_despesas * 100) if total_despesas > 0 else 0
            st.write(f"• **{cat}**: {valor:,.2f} € ({pct:.1f}%)")

    st.markdown("---")

    # === ÚLTIMOS REGISTOS ===
    st.markdown("### 📋 Últimos Registos")
    
    ultimos = df_analise.sort_values('Data', ascending=False).head(10)
    
    if not ultimos.empty:
        # Simplificar a tabela
        cols_show = ['Pessoa', 'Tipo', 'Categoria', 'Valor', 'Data']
        cols_exist = [c for c in cols_show if c in ultimos.columns]
        df_view = ultimos[cols_exist].copy()
        # Formatar data para mostrar apenas dia/mês/ano
        if 'Data' in df_view.columns:
            df_view['Data'] = pd.to_datetime(df_view['Data']).dt.strftime('%d-%m-%Y')
        st.dataframe(df_view, use_container_width=True)

    st.markdown("---")

    # === EXPORTAR ===
    st.markdown("### 📥 Exportar Dados")
    
    csv = df_analise.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Descarregar CSV",
        data=csv,
        file_name="finance_app_export.csv",
        mime="text/csv",
        key="export_csv"
    )

    st.stop()

# =========================
# INDIVIDUAL
# =========================
pessoa = modo.split()[0]

st.subheader(f"{avatars.get(pessoa,'👤')} {pessoa}")

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"], key="tipo_select")

categoria = ""
descricao = ""

if tipo == "Despesa":
    # Adicionar "Outros" à lista de categorias se não existir
    todas_categorias = categories + ["Outros"] if categories else ["Outros"]
    categoria = st.selectbox(
        "Categoria", 
        todas_categorias,
        key="cat_select"
    )
    
    # Só mostrar descrição quando selecionar "Outros"
    if categoria == "Outros":
        descricao = st.text_input(
            "Descrição (especifique)", 
            value=st.session_state.inputs.get('descricao', ''),
            key="desc_input"
        )
    else:
        # Limpar descrição se não for "Outros"
        descricao = ""
        if 'descricao' in st.session_state.inputs:
            st.session_state.inputs['descricao'] = ''

valor = st.number_input(
    "Valor (€)", 
    min_value=0.0,
    value=st.session_state.inputs.get('valor', 0.0),
    key="valor_input"
)

# Data máxima = hoje (não permite datas futuras)
data_max = datetime.today().date()
data = st.date_input("Data", datetime.today(), key="data_input")

# Validação
erros = []

if valor <= 0:
    erros.append("O valor deve ser maior que 0")

if valor > 10000:
    st.warning("⚠️ Valor elevado! Confirme que está correto.")

if tipo == "Despesa" and not categoria:
    erros.append("Selecione uma categoria")

if tipo == "Despesa" and categoria == "Outros" and not descricao.strip():
    erros.append("Adicione uma descrição")

if erros:
    for erro in erros:
        st.error(erro)

if st.button("Adicionar", key="adicionar"):
    if valor > 0 and (tipo != "Despesa" or (categoria and (categoria != "Outros" or descricao.strip()))):
        sheet.append_row([
            generate_id(),
            pessoa,
            tipo,
            categoria,
            descricao,
            float(valor),
            str(data)
        ])
        reset_inputs()
        # Limpar cache antes de atualizar
        load_data.clear()
        st.success("✅ Registado com sucesso!")
        time.sleep(1)
        refresh()
    else:
        st.error("Por favor, preencha todos os campos corretamente")

# Info de cache (debug opcional)
with st.sidebar.expander("ℹ️ Info"):
    st.caption("Dados em cache por 5 minutos para evitar exceder limites da API Google")
