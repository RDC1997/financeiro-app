import streamlit as st
import pandas as pd
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(page_title="Rubi&Gabi Finance", layout="wide")
st.title("💰 Controlo Financeiro")

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

    sheet = client.open_by_key(
        "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
    ).sheet1

    cat_sheet = client.open_by_key(
        "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
    ).worksheet("Categorias")

    goals_sheet = client.open_by_key(
        "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
    ).worksheet("Metas")

except Exception as e:
    st.error(f"❌ Erro ao ligar ao Google Sheets: {e}")
    st.stop()

# =========================
# CATEGORIAS
# =========================
@st.cache_data(ttl=10)
def load_categories():
    data = cat_sheet.get_all_values()
    if len(data) < 2:
        return []
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
# METAS
# =========================
@st.cache_data(ttl=10)
def load_goals():
    data = goals_sheet.get_all_values()

    if len(data) < 2:
        return pd.DataFrame(columns=["Nome","Objetivo","Atual"])

    df = pd.DataFrame(data[1:], columns=data[0])
    df["Objetivo"] = pd.to_numeric(df["Objetivo"], errors="coerce").fillna(0)
    df["Atual"] = pd.to_numeric(df["Atual"], errors="coerce").fillna(0)

    return df

goals = load_goals()

# =========================
# DATA
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()

    expected_cols = [
        "Pessoa",
        "Tipo",
        "Categoria",
        "Descrição",
        "Valor",
        "Data"
    ]

    if not raw or len(raw) < 2:
        return pd.DataFrame(columns=expected_cols)

    headers = [h.strip() for h in raw[0]]
    df = pd.DataFrame(raw[1:], columns=headers)

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    df["Pessoa"] = df["Pessoa"].astype(str).str.strip()
    df["Tipo"] = df["Tipo"].astype(str).str.strip()
    df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df["Descrição"] = df["Descrição"].astype(str).fillna("")
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date

    df["sheet_row"] = df.index + 2

    return df

df = load_data()

# =========================
# DELETE
# =========================
def delete_row_safe(row):
    try:
        sheet.delete_rows(int(row))
        return True
    except Exception as e:
        st.error(f"Erro ao eliminar: {e}")
        return False

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## ⚙️ Menu")

modo = st.sidebar.selectbox(
    "Escolhe área",
    [
        "👩‍❤️‍👨 Casal",
        "🤴 Ruben",
        "👸 Gabi",
        "🎯 Metas"
    ]
)

# =========================
# CASAL
# =========================
if modo == "👩‍❤️‍👨 Casal":

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

        return df[(df["Pessoa"] == pessoa) & (df["Data"] >= last_salary)]

    for pessoa in ["Ruben", "Gabi"]:

        df_p = filtrar_ciclo(df, pessoa)

        st.markdown(f"## {pessoa}")

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        st.markdown("### 💰 Receitas")
        st.dataframe(receitas)

        st.markdown("### 💸 Despesas")
        st.dataframe(despesas)

        st.markdown(f"**Total: € {despesas['Valor'].sum():.2f}**")

    st.stop()

# =========================
# METAS
# =========================
if modo == "🎯 Metas":

    st.subheader("🎯 Metas do Casal")

    st.stop()

# =========================
# RUBEN / GABI
# =========================
st.subheader(modo)

pessoa = modo.replace("🤴","").replace("👸","").strip()

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":
    if categories:
        categoria = st.selectbox("Categoria", categories)
    else:
        categoria = st.text_input("Categoria")

    descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):
    sheet.append_row([pessoa, tipo, categoria, descricao, float(valor), str(data)])
    st.cache_data.clear()
    st.rerun()

# =========================
# ELIMINAR
# =========================
st.markdown("---")
st.subheader("🗑 Eliminar")

df_user = df[df["Pessoa"] == pessoa]

for _, row in df_user.iterrows():

    c1, c2, c3, c4, c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(f"€ {row['Valor']:.2f}")

    if c5.button("❌", key=row["sheet_row"]):
        delete_row_safe(row["sheet_row"])
        st.cache_data.clear()
        st.rerun()
