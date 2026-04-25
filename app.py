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

except Exception:
    st.error("❌ Erro ao ligar ao Google Sheets")
    st.stop()

# =========================
# DATA (ROBUSTO)
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
# 🟢 CASAL
# =========================
if modo == "Casal":

    st.subheader("📊 Visão Geral")

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = df[df.get("Pessoa", "") == pessoa]

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        # =========================
        # 💰 RECEITAS
        # =========================
        st.markdown("### 💰 Receitas")

        if not receitas.empty:
            st.table(receitas[["Tipo","Valor","Data"]])
        else:
            st.info("Sem receitas")

        # =========================
        # 💸 DESPESAS
        # =========================
        st.markdown("### 💸 Despesas")

        if not despesas.empty:

            despesas = despesas.copy()

            despesas["Categoria"] = despesas.apply(
                lambda r: (
                    f"{icons.get(r['Categoria'],'')} {r['Categoria']} - {r['Descrição']}"
                    if r["Categoria"] == "Outros" and str(r["Descrição"]).strip() != ""
                    else f"{icons.get(r['Categoria'],'')} {r['Categoria']}"
                ),
                axis=1
            )

            st.table(despesas[["Categoria","Valor","Data"]])

            total = despesas["Valor"].sum()
            st.markdown(f"### 💰 Total de Despesas: **€ {total:.2f}**")

        else:
            st.info("Sem despesas")

    st.stop()

# =========================
# 🔵 GESTÃO
# =========================
st.subheader(f"{avatars[modo]} {modo}")

pessoa = modo

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox("Categoria", list(icons.keys()))

    if categoria == "Outros":
        descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

# ❌ bloquear datas futuras
if data > datetime.today().date():
    st.error("Não podes escolher data futura")
    st.stop()

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
    st.success("Adicionado com sucesso")
    st.rerun()

# =========================
# 🗑 ELIMINAR
# =========================
st.markdown("---")
st.subheader("🗑 Eliminar registos")

for _, row in df[df.get("Pessoa", "") == modo].iterrows():

    c1, c2, c3, c4, c5 = st.columns([2,3,2,2,1])

    c1.write(row.get("Pessoa",""))
    c2.write(row.get("Tipo",""))
    c3.write(row.get("Categoria",""))
    c4.write(row.get("Valor",""))

    if c5.button("❌", key=f"del_{row.get('sheet_row',_)}"):
        sheet.delete_rows(row.get("sheet_row", _ + 2))
        st.cache_data.clear()
        st.success("Eliminado")
        st.rerun()
