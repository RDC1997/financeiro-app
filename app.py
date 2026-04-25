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
    st.stop()

# =========================
# DATA
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
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    df["sheet_row"] = df.index + 2

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

def eliminar_linha(row):
    sheet.delete_rows(row)

df = load_data()

# =========================
# ICONS
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
# FILTRO MÊS
# =========================
if not df.empty:
    df["Mes"] = df["Data"].dt.to_period("M").astype(str)

    meses = sorted(df["Mes"].dropna().unique())
    mes = st.sidebar.selectbox("Mês", ["Atual"] + meses)

    if mes == "Atual":
        atual = str(pd.Timestamp.today().to_period("M"))
        df = df[df["Mes"] == atual]
    else:
        df = df[df["Mes"] == mes]

# =========================
# 🟢 CASAL (CORRIGIDO)
# =========================
if modo == "Casal":

    st.subheader("📊 Dashboard")

    receitas = df[df["Tipo"].isin(["Salário","Subsídio Alimentação"])]
    despesas = df[df["Tipo"] == "Despesa"]

    st.metric("💰 Receitas", f"€ {receitas['Valor'].sum():.2f}")
    st.metric("💸 Despesas", f"€ {despesas['Valor'].sum():.2f}")

    st.markdown("---")

    # =========================
    # RECEITAS (RESTAUROU)
    # =========================
    st.markdown("## 💰 Receitas")

    if not receitas.empty:
        st.table(receitas[["Pessoa","Tipo","Valor","Data"]])
    else:
        st.info("Sem receitas")

    # =========================
    # DESPESAS
    # =========================
    st.markdown("## 💸 Despesas")

    if not despesas.empty:

        despesas = despesas.copy()

        despesas["Categoria"] = despesas.apply(
            lambda r: f"{icons.get(r['Categoria'],'')} {r['Categoria']} - {r['Descrição']}"
            if r["Categoria"] == "Outros" and r["Descrição"]
            else f"{icons.get(r['Categoria'],'')} {r['Categoria']}",
            axis=1
        )

        st.table(despesas[["Pessoa","Categoria","Valor","Data"]])

    else:
        st.info("Sem despesas")

    st.stop()

# =========================
# 🔵 GESTÃO (CORRIGIDO OUTROS + DATA)
# =========================
st.subheader("➕ Novo registo")

pessoa = modo

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox("Categoria", list(icons.keys()))

    if categoria == "Outros":
        descricao = st.text_input("Descrição obrigatória")

valor = st.number_input("Valor (€)", min_value=0.0)

# 🔒 BLOQUEIO DATA FUTURA
data = st.date_input("Data", datetime.today())

if data > datetime.today().date():
    st.error("Não podes escolher uma data futura")
    st.stop()

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

# =========================
# 🗑 ELIMINAR
# =========================
st.markdown("---")
st.subheader("🗑 Eliminar registos")

for _, row in df.iterrows():

    c1, c2, c3, c4, c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(row["Valor"])

    if c5.button("❌", key=f"del_{row['sheet_row']}"):
        eliminar_linha(row["sheet_row"])
        st.cache_data.clear()
        st.success("Eliminado")
        st.rerun()
