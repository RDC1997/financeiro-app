import streamlit as st
import pandas as pd
from datetime import datetime
import time
import uuid

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(page_title="Rubi&Gabi Finance", layout="wide")
st.title("💰 Controlo Financeiro")

# =========================
# HELPERS
# =========================
def safe_sleep():
    time.sleep(0.3)

def refresh():
    st.cache_data.clear()
    st.rerun()

def generate_id():
    return str(uuid.uuid4())

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
# CATEGORIAS (RESTAURADO COMPLETO)
# =========================
@st.cache_data(ttl=30)
def load_categories():
    data = cat_sheet.get_all_values()
    return [row[0] for row in data[1:] if row[0].strip() != ""]

def add_category(cat):
    safe_sleep()
    cat_sheet.append_row([cat])

def delete_category(cat):
    safe_sleep()
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
# CATEGORIAS UI (RESTAURADO)
# =========================
st.sidebar.markdown("## ⚙️ Categorias")

with st.sidebar.expander("➕ Adicionar categoria"):
    new_cat = st.text_input("Nova categoria")

    if st.button("Adicionar"):
        if new_cat.strip():
            add_category(new_cat.strip())
            refresh()

with st.sidebar.expander("❌ Remover categoria"):
    if categories:
        cat_del = st.selectbox("Escolher", categories)

        if st.button("Remover"):
            delete_category(cat_del)
            refresh()

with st.sidebar.expander("📋 Ver categorias"):
    st.write(categories)

# =========================
# CASAL (CORRIGIDO - LÓGICA MENSAL)
# =========================
if modo == "Casal 👨‍❤️‍👩":

    st.subheader("👨‍❤️‍👩 Casal - Visão Mensal")

    mes_atual = datetime.today().month

    for p in ["Ruben","Gabi"]:

        st.markdown(f"## {avatars[p]} {p}")

        df_p = df[df["Pessoa"] == p]
        df_mes = df_p[pd.to_datetime(df_p["Data"]).dt.month == mes_atual]

        receitas = df_mes[df_mes["Tipo"] != "Despesa"]
        despesas = df_mes[df_mes["Tipo"] == "Despesa"]

        st.markdown("### 📅 Mês atual")

        st.write("#### 💰 Receitas")
        st.dataframe(receitas, use_container_width=True)

        st.write("#### 💸 Despesas")
        st.dataframe(despesas, use_container_width=True)

        st.write(f"**Total despesas: € {despesas['Valor'].sum():.2f}**")

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
        nome = st.text_input("Nome")
        obj = st.number_input("Objetivo (€)", min_value=0.0)

        if st.button("Criar"):
            goal_sheet.append_row([nome,obj,0])
            refresh()

    st.dataframe(goals)

    st.stop()

# =========================
# INDIVIDUAL
# =========================
pessoa = modo.split()[0]

st.subheader(f"{avatars.get(pessoa,'👤')} {pessoa}")

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox("Categoria", categories if categories else ["Outros"])
    descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):
    sheet.append_row([
        generate_id(),
        pessoa,
        tipo,
        categoria,
        descricao,
        float(valor),
        str(data)
    ])
    refresh()

# =========================
# DELETE
# =========================
st.markdown("---")
st.subheader("🗑 Registos")

df_user = df[df["Pessoa"] == pessoa]

for _, row in df_user.sort_values("Data", ascending=False).iterrows():

    c1,c2,c3,c4,c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(f"{row['Valor']:.2f} €")

    if c5.button("❌", key=row["ID"]):
        data = sheet.get_all_values()
        headers = data[0]
        id_index = headers.index("ID")

        for i, r in enumerate(data[1:], start=2):
            if r[id_index] == row["ID"]:
                sheet.delete_rows(i)
                break

        refresh()
