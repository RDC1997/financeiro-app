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

except Exception as e:
    st.error(f"❌ Erro ao ligar ao Google Sheets: {e}")
    st.stop()

# =========================
# CATEGORIAS (MANTIDO + GESTÃO)
# =========================
@st.cache_data(ttl=20)
def load_categories():
    data = cat_sheet.get_all_values()
    return [r[0] for r in data[1:] if r[0].strip()] if len(data) > 1 else []

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
@st.cache_data(ttl=20)
def load_data():
    raw = sheet.get_all_values()

    cols = ["Pessoa","Tipo","Categoria","Descrição","Valor","Data"]

    df = pd.DataFrame(raw[1:], columns=raw[0]) if len(raw) > 1 else pd.DataFrame(columns=cols)

    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date
    df["sheet_row"] = df.index + 2

    return df

df = load_data()

# =========================
# SAFE ACTIONS
# =========================
def delete_row(row):
    try:
        sheet.delete_rows(int(row))
        return True
    except:
        return False

def update_row(row_number, values):
    sheet.update(f"A{row_number}:F{row_number}", [values])

# =========================
# SESSION EDIT
# =========================
if "edit_row" not in st.session_state:
    st.session_state.edit_row = None

# =========================
# SIDEBAR CATEGORIAS (MANTIDO)
# =========================
st.sidebar.markdown("## ⚙️ Categorias")

with st.sidebar.expander("➕ Adicionar"):
    nova = st.text_input("Nova categoria")
    if st.button("Adicionar categoria"):
        if nova.strip():
            add_category(nova.strip())
            st.cache_data.clear()
            st.rerun()

with st.sidebar.expander("❌ Remover"):
    if categories:
        cat = st.selectbox("Categoria", categories)
        if st.button("Remover categoria"):
            delete_category(cat)
            st.cache_data.clear()
            st.rerun()

# =========================
# MODO
# =========================
modo = st.sidebar.selectbox("Modo", ["Casal","Ruben","Gabi"])

avatars = {"Ruben":"🤴","Gabi":"👸"}

# =========================
# CASAL
# =========================
if modo == "Casal":
    st.subheader("📊 Casal")

    for p in ["Ruben","Gabi"]:
        st.markdown(f"## {avatars[p]} {p}")
        df_p = df[df["Pessoa"] == p]

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        st.metric("Receitas", f"€ {receitas['Valor'].sum():.2f}")
        st.metric("Despesas", f"€ {despesas['Valor'].sum():.2f}")

    st.stop()

# =========================
# INDIVIDUAL
# =========================
st.subheader(f"{avatars[modo]} {modo}")

df_user = df[df["Pessoa"] == modo]

# =========================
# EDITAR (NOVO MAS SEM REMOVER NADA)
# =========================
if st.session_state.edit_row:
    row = df[df["sheet_row"] == st.session_state.edit_row].iloc[0]

    st.markdown("## ✏️ Editar")

    tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])
    categoria = st.text_input("Categoria", value=row["Categoria"])
    descricao = st.text_input("Descrição", value=row["Descrição"])
    valor = st.number_input("Valor", value=float(row["Valor"]))
    data = st.date_input("Data", value=row["Data"])

    if st.button("Guardar"):
        update_row(
            st.session_state.edit_row,
            [row["Pessoa"], tipo, categoria, descricao, valor, str(data)]
        )
        st.session_state.edit_row = None
        st.cache_data.clear()
        st.rerun()

    if st.button("Cancelar"):
        st.session_state.edit_row = None

# =========================
# LISTA (MANTÉM DELETE)
# =========================
st.markdown("---")
st.subheader("📋 Registos")

for _, r in df_user.iterrows():

    c1,c2,c3,c4,c5,c6 = st.columns([2,2,2,2,1,1])

    c1.write(r["Tipo"])
    c2.write(r["Categoria"])
    c3.write(r["Descrição"])
    c4.write(f"€ {r['Valor']:.2f}")

    if c5.button("✏️", key=f"e_{r['sheet_row']}"):
        st.session_state.edit_row = r["sheet_row"]
        st.rerun()

    if c6.button("❌", key=f"d_{r['sheet_row']}"):
        delete_row(r["sheet_row"])
        st.cache_data.clear()
        st.rerun()

# =========================
# ADICIONAR (MANTIDO)
# =========================
st.markdown("---")
st.subheader("➕ Adicionar")

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])

if tipo == "Despesa" and categories:
    categoria = st.selectbox("Categoria", categories)
else:
    categoria = st.text_input("Categoria")

descricao = st.text_input("Descrição")
valor = st.number_input("Valor")
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):

    sheet.append_row([
        modo,
        tipo,
        categoria,
        descricao,
        float(valor),
        str(data)
    ])

    st.cache_data.clear()
    st.rerun()
