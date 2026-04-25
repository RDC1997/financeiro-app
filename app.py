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

    sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").sheet1
    cat_sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").worksheet("Categorias")

    # METAS
    try:
        goal_sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").worksheet("Metas")
    except:
        goal_sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").add_worksheet("Metas", 100, 3)
        goal_sheet.append_row(["Meta","Objetivo","Atual"])

except Exception as e:
    st.error(f"❌ Erro ao ligar ao Google Sheets: {e}")
    st.stop()

# =========================
# CATEGORIAS (INTACTO)
# =========================
@st.cache_data(ttl=10)
def load_categories():
    data = cat_sheet.get_all_values()
    if len(data) < 2:
        return []
    return [row[0] for row in data[1:] if row[0].strip()]

def add_category(cat):
    cat_sheet.append_row([cat])

def delete_category(cat):
    data = cat_sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == cat:
            cat_sheet.delete_rows(i+1)
            break

categories = load_categories()

# =========================
# DATA (INTACTO)
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()

    expected_cols = ["Pessoa","Tipo","Categoria","Descrição","Valor","Data"]

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
# METAS
# =========================
def load_goals():
    data = goal_sheet.get_all_records()
    return pd.DataFrame(data)

def update_goal(row, value):
    goal_sheet.update_cell(row, 3, value)

def delete_goal(row):
    goal_sheet.delete_rows(row)

goals = load_goals()

# =========================
# DELETE SAFE
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
modo = st.sidebar.selectbox("Modo", ["Casal 👨‍❤️‍👩", "Ruben 🤴", "Gabi 👸", "Metas 🎯"])

# =========================
# METAS
# =========================
if modo == "Metas 🎯":

    st.subheader("🎯 Metas Financeiras")

    with st.expander("➕ Criar meta"):
        nome = st.text_input("Nome")
        objetivo = st.number_input("Objetivo (€)", min_value=0.0)

        if st.button("Criar"):
            goal_sheet.append_row([nome, objetivo, 0])
            st.rerun()

    for i, row in goals.iterrows():

        meta = row["Meta"]
        obj = float(row["Objetivo"])
        atual = float(row["Atual"])

        percent = (atual / obj * 100) if obj > 0 else 0

        if percent < 25:
            emoji = "🔴"
        elif percent < 50:
            emoji = "🟠"
        elif percent < 75:
            emoji = "🟡"
        else:
            emoji = "🟢"

        st.write(f"### {meta}")
        st.progress(min(percent/100,1))
        st.write(f"{emoji} {percent:.1f}% — € {atual} / € {obj}")

        col1, col2 = st.columns(2)

        add = col1.number_input("Adicionar", min_value=0.0, key=f"a{i}")

        if col1.button("Adicionar dinheiro", key=f"b{i}"):
            goal_sheet.update_cell(i+2, 3, atual + add)
            st.rerun()

        if col2.button("Eliminar", key=f"c{i}"):
            delete_goal(i+2)
            st.rerun()

    st.stop()

# =========================
# CASAL / RUBEN / GABI (RESTAURADO)
# =========================
avatars = {
    "Ruben": "🤴",
    "Gabi": "👸"
}

st.subheader(f"{avatars.get(modo.split()[0], '👨‍❤️‍👩')} {modo}")

pessoa = modo.split()[0]

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox("Categoria", categories if categories else ["Outros"])
    descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):
    sheet.append_row([pessoa,tipo,categoria,descricao,float(valor),str(data)])
    st.rerun()

st.markdown("---")
st.subheader("🗑 Eliminar registos")

df_user = df[df["Pessoa"] == pessoa].sort_values("Data", ascending=False)

for _, row in df_user.iterrows():

    c1,c2,c3,c4,c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(f"€ {row['Valor']:.2f}")

    if c5.button("❌", key=row["sheet_row"]):
        delete_row_safe(row["sheet_row"])
        st.rerun()
