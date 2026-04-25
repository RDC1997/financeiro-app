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
# CATEGORIAS UI
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
# CASAL (SUBSTITUÍDO COMO PEDISTE)
# =========================
if modo == "Casal 👨‍❤️‍👩":

    st.subheader("📊 Visão Geral (Ciclos por salário)")

    def get_last_salary(df, pessoa):
        df_p = df[(df["Pessoa"] == pessoa) & (df["Tipo"] == "Salário")]
        if df_p.empty:
            return None
        return df_p.sort_values("Data", ascending=False).iloc[0]["Data"]

    def filtrar_ciclo(df, pessoa):
        last_salary = get_last_salary(df, pessoa)

        if not last_salary:
            return df[df["Pessoa"] == pessoa]

        return df[
            (df["Pessoa"] == pessoa) &
            (df["Data"] >= last_salary)
        ]

    for pessoa in ["Ruben","Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = filtrar_ciclo(df, pessoa)

        with st.expander(f"🔍 Debug do ciclo - {pessoa}"):
            st.write("Último salário:", get_last_salary(df, pessoa))
            st.write("Registos no ciclo:", len(df_p))
            st.dataframe(df_p[["Tipo","Valor","Data"]])

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        st.markdown("### 💰 Receitas")

        if not receitas.empty:
            st.dataframe(receitas[["Tipo","Valor","Data"]], use_container_width=True)
        else:
            st.info("Sem receitas neste ciclo")

        st.markdown("### 💸 Despesas")

        if not despesas.empty:
            st.dataframe(despesas[["Categoria","Valor","Data"]], use_container_width=True)

            total = despesas["Valor"].sum()
            st.markdown(f"### 💰 Total de Despesas: **€ {total:.2f}**")
        else:
            st.info("Sem despesas neste ciclo")

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
