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

except Exception as e:
    st.error("❌ Erro ao ligar ao Google Sheets")
    st.error(str(e))
    st.stop()

# =========================
# CACHE
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(raw[1:], columns=raw[0])
    df.columns = df.columns.str.strip()

    df["Pessoa"] = df["Pessoa"].astype(str).str.strip()
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

    # 🔧 DATA LIMPA
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    return df

def guardar(d):
    sheet.append_row([
        d["Pessoa"],
        d["Tipo"],
        d["Categoria"],
        d["Descrição"],
        float(d["Valor"]),
        str(d["Data"])
    ])

df = load_data()

# =========================
# ÍCONES
# =========================
icons = {
    "Renda": "🏠",
    "Vodafone": "📱",
    "Gasolina": "🚗",
    "Alimentação": "🛒",
    "Luz": "💡",
    "Água": "🚿",
    "Outros": "📦"
}

avatars = {
    "Ruben": "🤴",
    "Gabi": "👸"
}

# =========================
# MODO
# =========================
modo = st.sidebar.selectbox("Modo", ["Casal", "Ruben", "Gabi"])

# =========================
# 📅 FILTRO POR MÊS
# =========================
if not df.empty and "Data" in df.columns:
    meses = sorted(df["Data"].dropna().dt.to_period("M").unique().astype(str))
    mes_escolhido = st.sidebar.selectbox("Mês", ["Atual"] + meses)

    if mes_escolhido == "Atual":
        hoje = pd.Timestamp.today().to_period("M")
        df = df[df["Data"].dt.to_period("M") == hoje]
    else:
        df = df[df["Data"].dt.to_period("M").astype(str) == mes_escolhido]

# =========================
# 🟢 CASAL (DASHBOARD LIMPO)
# =========================
if modo == "Casal":

    st.subheader("📊 Dashboard Mensal")

    receitas = df[df["Tipo"].isin(["Salário", "Subsídio Alimentação"])]["Valor"].sum()
    despesas = df[df["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = receitas - despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Receitas", f"€ {receitas:.2f}")
    col2.metric("💸 Despesas", f"€ {despesas:.2f}")
    col3.metric("⚖️ Saldo", f"€ {saldo:.2f}")

    st.markdown("---")

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = df[df["Pessoa"] == pessoa]

        r = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]["Valor"].sum()
        d = df_p[df_p["Tipo"] == "Despesa"]["Valor"].sum()

        c1, c2 = st.columns(2)
        c1.metric("💰 Receitas", f"€ {r:.2f}")
        c2.metric("💸 Despesas", f"€ {d:.2f}")

        st.markdown("---")

    st.stop()

# =========================
# 🔵 GESTÃO (R / G)
# =========================
st.subheader("➕ Novo registo")

pessoa = modo

tipo = st.selectbox("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox("Categoria", list(icons.keys()))

    if categoria == "Outros":
        descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):
    guardar({
        "Pessoa": pessoa,
        "Tipo": tipo,
        "Categoria": categoria,
        "Descrição": descricao,
        "Valor": valor,
        "Data": data
    })

    st.cache_data.clear()
    st.success("Adicionado com sucesso")
    st.rerun()
