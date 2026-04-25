import streamlit as st
import pandas as pd
from datetime import datetime
import io

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

except Exception:
    st.error("❌ Erro ao ligar ao Google Sheets")
    st.stop()

# =========================
# DATA
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
# CATEGORIAS (NOVO - SEM REMOVER FIXAS)
# =========================
@st.cache_data(ttl=30)
def load_categories():
    fixed = ["Renda","Vodafone","Gasolina","Alimentação","Luz","Água","Outros"]

    try:
        data = cat_sheet.get_all_values()
        sheet_cats = [r[0] for r in data[1:] if r and r[0].strip()]
    except:
        sheet_cats = []

    return list(dict.fromkeys(fixed + sheet_cats))

categories = load_categories()

# =========================
# OBJETIVOS FINANCEIROS (NOVO)
# =========================
st.sidebar.markdown("## 🎯 Objetivos")

goal = st.sidebar.number_input("Objetivo mensal (€)", min_value=0.0)

# =========================
# CICLO
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
# MODO
# =========================
modo = st.sidebar.selectbox("Modo", ["Casal", "Ruben", "Gabi"])

avatars = {"Ruben":"🤴","Gabi":"👸"}

# =========================
# CASAL
# =========================
if modo == "Casal":

    st.subheader("📊 Dashboard Casal")

    total_r = df[df["Tipo"].isin(["Salário","Subsídio Alimentação"])]["Valor"].sum()
    total_d = df[df["Tipo"]=="Despesa"]["Valor"].sum()

    st.metric("Receitas", f"€ {total_r:.2f}")
    st.metric("Despesas", f"€ {total_d:.2f}")

    if goal > 0:
        st.progress(min(total_d / goal, 1.0))
        st.write(f"Objetivo: € {goal}")

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
    sheet.append_row([
        pessoa,
        tipo,
        categoria,
        descricao,
        float(valor),
        str(data)
    ])

    st.cache_data.clear()
    st.rerun()

# =========================
# 🗑 ELIMINAR
# =========================
st.markdown("---")
st.subheader("🗑 Registos")

df_user = df[df.get("Pessoa","") == modo]

for _, row in df_user.iterrows():

    c1,c2,c3,c4,c5 = st.columns([2,3,2,2,1])

    c1.write(row["Tipo"])
    c2.write(row["Categoria"])
    c3.write(row["Descrição"])
    c4.write(row["Valor"])

    if c5.button("❌", key=f"del_{row['sheet_row']}"):
        sheet.delete_rows(row["sheet_row"])
        st.cache_data.clear()
        st.rerun()

# =========================
# 📅 HISTÓRICO MENSAL (NOVO)
# =========================
st.markdown("---")
st.subheader("📅 Histórico mensal")

df["Mes"] = pd.to_datetime(df["Data"]).dt.to_period("M").astype(str)

hist = df.groupby("Mes")["Valor"].sum()

st.line_chart(hist)

# =========================
# 📁 EXPORTAÇÃO (NOVO)
# =========================
st.markdown("---")
st.subheader("📁 Exportar dados")

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Exportar CSV",
    csv,
    "finance.csv",
    "text/csv"
)

# Excel
output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False)

st.download_button(
    "Exportar Excel",
    output.getvalue(),
    "finance.xlsx"
)
