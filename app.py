import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import plotly.express as px

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(page_title="Rubi&Gabi Finance PRO 2.1", layout="wide")
st.title("💰 Controlo Financeiro ")

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

# =========================
# HELPERS
# =========================
def refresh():
    st.cache_data.clear()
    st.rerun()

def generate_id():
    return str(uuid.uuid4())

def reset_inputs():
    st.session_state.inputs = {
        'valor': 0.0,
        'descricao': '',
        'categoria': ''
    }

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
@st.cache_data(ttl=30)
def load_categories():
    data = cat_sheet.get_all_values()
    return [row[0] for row in data[1:] if row[0].strip() != ""]

def add_category(cat):
    cat_sheet.append_row([cat])

def delete_category(cat):
    data = cat_sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == cat:
            cat_sheet.delete_rows(i + 1)
            break

categories = load_categories()

# =========================
# DATA
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()
    cols = ["ID","Pessoa","Tipo","Categoria","Descrição","Valor","Data"]

    if len(raw) < 2:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(raw[1:], columns=raw[0])

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date

    return df

df = load_data()

# =========================
# MENU
# =========================
modo = st.sidebar.selectbox(
    "Modo",
    ["Casal 👨‍❤️‍👩","Ruben 🤴","Gabi 👸","Metas 🎯"]
)

avatars = {"Ruben":"🤴","Gabi":"👸"}

# =========================
# CATEGORIAS UI
# =========================
st.sidebar.markdown("## ⚙️ Categorias")

with st.sidebar.expander("➕ Adicionar categoria"):
    new_cat = st.text_input("Nova categoria")

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
    st.write(categories if categories else "Sem categorias")

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

    # Processar cada pessoa em separado para evitar problemas de renderização
    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"### {avatars[pessoa]} {pessoa}")

        df_p = filtrar_ciclo(df, pessoa)

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
                st.dataframe(
                    receitas.drop(columns=[c for c in ["ID"] if c in receitas.columns]),
                    use_container_width=True
                )
            else:
                st.info("Sem receitas neste ciclo")

        with st.expander("💸 Despesas"):
            if not despesas.empty:
                st.dataframe(
                    despesas.drop(columns=[c for c in ["ID"] if c in despesas.columns]),
                    use_container_width=True
                )
            else:
                st.info("Sem despesas neste ciclo")

        with st.expander("🗑 Eliminar registos"):
            if not df_p.empty:
                st.warning("⚠️ Clique no botão para eliminar um registo")
                
                # Usar container para evitar problemas com keys duplicadas
                for idx, (_, row) in enumerate(df_p.iterrows()):
                    with st.container():
                        c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])
                        
                        c1.write(row["Pessoa"])
                        c2.write(row["Tipo"])
                        c3.write(row["Categoria"])
                        c4.write(f"{row['Valor']:.2f} €")
                        
                        # Verificar se há confirmação pendente
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
        # Calcular progresso
        if not goals.empty and 'Objetivo' in goals.columns:
            goals['Progresso'] = goals.apply(
                lambda x: (x.get('Atual', 0) / x['Objetivo'] * 100) if x['Objetivo'] > 0 else 0, 
                axis=1
            )
        
        st.dataframe(goals, use_container_width=True)
        
        # Gráfico de progresso
        if not goals.empty:
            st.markdown("### 📈 Progresso das Metas")
            for _, goal in goals.iterrows():
                objetivo = float(goal.get('Objetivo', 0))
                atual = float(goal.get('Atual', 0))
                progresso = min((atual / objetivo * 100), 100) if objetivo > 0 else 0
                
                st.progress(int(progresso), text=f"{goal['Meta']}: {progresso:.1f}% ({atual:.2f}€ / {objetivo:.2f}€)")

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
    categoria = st.selectbox(
        "Categoria", 
        categories if categories else ["Outros"],
        key="cat_select"
    )
    descricao = st.text_input(
        "Descrição", 
        value=st.session_state.inputs.get('descricao', ''),
        key="desc_input"
    )

valor = st.number_input(
    "Valor (€)", 
    min_value=0.0,
    value=st.session_state.inputs.get('valor', 0.0),
    key="valor_input"
)

data = st.date_input("Data", datetime.today(), key="data_input")

# Validação
erros = []

if valor <= 0:
    erros.append("O valor deve ser maior que 0")

if tipo == "Despesa" and not categoria:
    erros.append("Selecione uma categoria")

if tipo == "Despesa" and not descricao.strip():
    erros.append("Adicione uma descrição")

# Mostrar erros
if erros:
    for erro in erros:
        st.error(erro)

if st.button("Adicionar", key="adicionar"):
    # Validação final
    if valor > 0 and (tipo != "Despesa" or (categoria and descricao.strip())):
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
        refresh()
    else:
        st.error("Por favor, preencha todos os campos corretamente")

# Mostrar último registo adicionado com sucesso
st.success("✅ Pronto para adicionar registos")
