import streamlit as st
import pandas as pd
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(page_title="Rubi&Gabi", layout="wide")
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
    spreadsheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME")
    sheet = spreadsheet.get_worksheet(0)

except Exception as e:
    st.error("❌ Erro ao ligar ao Google Sheets")
    st.error(str(e))
    st.stop()

# =========================
# CACHE (🔥 FIX DO ERRO 429)
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

    return df

# =========================
# SAVE
# =========================
def guardar(d):
    sheet.append_row([
        d["Pessoa"],
        d["Tipo"],
        d["Categoria"],
        d["Descrição"],
        float(d["Valor"]),
        str(d["Data"])
    ])

# =========================
# LOAD (AGORA COM CACHE)
# =========================
df = load_data()

# =========================
# MODO
# =========================
modo = st.sidebar.selectbox("Modo", ["Casal", "Ruben", "Gabi"], key="modo")

df_view = df.copy()

if not df_view.empty:
    if modo == "Ruben":
        df_view = df_view[df_view["Pessoa"] == "Ruben"]
    elif modo == "Gabi":
        df_view = df_view[df_view["Pessoa"] == "Gabi"]

# =========================
# CASAL (SÓ LEITURA)
# =========================
if modo == "Casal":

    st.subheader("📊 Visão Geral")

    receitas = df[df["Tipo"].isin(["Salário", "Subsídio Alimentação"])]["Valor"].sum()
    despesas = df[df["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Receitas", f"€ {receitas:.2f}")
    c2.metric("💸 Despesas", f"€ {despesas:.2f}")
    c3.metric("⚖️ Saldo", f"€ {saldo:.2f}")

    st.markdown("---")

    st.subheader("📈 Receitas")
    st.bar_chart(df[df["Tipo"].isin(["Salário","Subsídio Alimentação"])].groupby("Pessoa")["Valor"].sum())

    st.subheader("📉 Despesas")
    st.bar_chart(df[df["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum())

    st.stop()

# =========================
# ADICIONAR
# =========================
st.subheader("➕ Novo registo")

pessoa = modo

tipo = st.selectbox("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"], key="tipo_add")

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox(
        "Categoria",
        ["Renda", "Água", "Luz", "Vodafone", "Alimentação", "Gasolina", "Outros"],
        key="cat_add"
    )

    if categoria == "Outros":
        descricao = st.text_input("Descrição", key="desc_add")

valor = st.number_input("Valor (€)", min_value=0.0, key="valor_add")
data = st.date_input("Data", datetime.today(), key="data_add")

if st.button("Adicionar", key="btn_add"):
    guardar({
        "Pessoa": pessoa,
        "Tipo": tipo,
        "Categoria": categoria,
        "Descrição": descricao,
        "Valor": valor,
        "Data": data
    })

    # 🔥 IMPORTANTE: limpa cache para atualizar dados
    st.cache_data.clear()

    st.success("Adicionado com sucesso")
    st.rerun()
