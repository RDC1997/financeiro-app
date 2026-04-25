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
# GOOGLE SHEETS (SAFE)
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

    # =========================
    # CATEGORIAS (SAFE FALLBACK)
    # =========================
    try:
        cat_sheet = client.open_by_key(
            "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
        ).worksheet("Categorias")
    except:
        cat_sheet = None

except Exception:
    st.error("❌ Erro ao ligar ao Google Sheets")
    st.stop()

# =========================
# CATEGORIAS (BLINDADO)
# =========================
@st.cache_data(ttl=30)
def load_categories():

    fixed = ["Renda","Vodafone","Gasolina","Alimentação","Luz","Água","Outros"]

    sheet_cats = []

    if cat_sheet is not None:
        try:
            data = cat_sheet.get_all_values()
            if len(data) > 1:
                sheet_cats = [r[0] for r in data[1:] if r and r[0].strip()]
        except:
            sheet_cats = []

    return list(dict.fromkeys(fixed + sheet_cats))

def add_category(cat):
    if cat_sheet:
        try:
            cat_sheet.append_row([cat])
        except:
            pass

def delete_category(cat):
    if not cat_sheet:
        return

    try:
        data = cat_sheet.get_all_values()

        for i, row in enumerate(data):
            if i == 0:
                continue
            if row and row[0] == cat:
                cat_sheet.delete_rows(i + 1)
                break
    except:
        pass

categories = load_categories()

# =========================
# DATA (SAFE)
# =========================
@st.cache_data(ttl=30)
def load_data():
    try:
        raw = sheet.get_all_values()
    except:
        return pd.DataFrame(columns=["Pessoa","Tipo","Categoria","Descrição","Valor","Data"])

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
# SAFE DELETE
# =========================
def safe_delete(row):
    try:
        sheet.delete_rows(int(row))
    except:
        pass

# =========================
# CICLO (MANTIDO)
# =========================
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

# =========================
# ICONS
# =========================
avatars = {"Ruben":"🤴","Gabi":"👸"}

# =========================
# MODO
# =========================
modo = st.sidebar.selectbox("Modo", ["Casal","Ruben","Gabi"])

# =========================
# CASAL
# =========================
if modo == "Casal":

    st.subheader("📊 Visão Geral")

    for pessoa in ["Ruben","Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = filtrar_ciclo(df, pessoa)

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        st.metric("💰 Receitas", f"€ {receitas['Valor'].sum():.2f}")
        st.metric("💸 Despesas", f"€ {despesas['Valor'].sum():.2f}")

    st.stop()

# =========================
# INDIVIDUAL
# =========================
st.subheader(f"{avatars[modo]} {modo}")

pessoa = modo

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox("Categoria", categories)

    if categoria == "Outros":
        descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):

    if tipo == "Despesa" and categoria == "Outros" and descricao.strip() == "":
        st.error("❌ Descrição obrigatória")
        st.stop()

    try:
        sheet.append_row([
            pessoa,
            tipo,
            categoria,
            descricao,
            float(valor),
            str(data)
        ])
    except:
        st.error("Erro ao guardar")

    st.cache_data.clear()
    st.rerun()

# =========================
# ELIMINAR
# =========================
st.markdown("---")
st.subheader("🗑 Eliminar registos")

df_user = df[df.get("Pessoa","") == modo]

for _, row in df_user.iterrows():

    c1,c2,c3,c4,c5 = st.columns([2,3,2,2,1])

    c1.write(row.get("Pessoa",""))
    c2.write(row.get("Tipo",""))
    c3.write(row.get("Categoria",""))
    c4.write(row.get("Valor",""))

    if c5.button("❌", key=f"del_{row['sheet_row']}"):
        safe_delete(row["sheet_row"])
        st.cache_data.clear()
        st.rerun()
