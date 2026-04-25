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

        df_p = df[df["Pessoa"] == pessoa]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        st.markdown("### 💸 Despesas")

        if not despesas.empty:

            despesas = despesas.copy()

            # =========================
            # DESCRIÇÃO + ÍCONE (CORRIGIDO)
            # =========================
            despesas["Categoria"] = despesas.apply(
                lambda r: (
                    f"{icons.get(r['Categoria'],'')} {r['Categoria']} - {r['Descrição']}"
                    if r["Categoria"] == "Outros" and str(r["Descrição"]).strip() != ""
                    else f"{icons.get(r['Categoria'],'')} {r['Categoria']}"
                ),
                axis=1
            )

            st.table(despesas[["Categoria","Valor","Data"]])

            # =========================
            # 🏆 RANKING (COM TOTAL)
            # =========================
            st.markdown("### 🏆 Ranking de Gastos")

            ranking = (
                despesas.groupby("Categoria")["Valor"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )

            # adicionar ícones ao ranking
            ranking["Categoria"] = ranking["Categoria"].apply(
                lambda x: f"{icons.get(x.replace('📦 ','').replace('🏠 ','').replace('🚗 ','').replace('🛒 ','').replace('💡 ','').replace('🚿 ','').replace('📱 ','').replace(' ','').split('-')[0].strip(), '')} {x}"
                if x != "💰 TOTAL"
                else x
            )

            # linha total
            total = pd.DataFrame({
                "Categoria": ["💰 TOTAL"],
                "Valor": [ranking["Valor"].sum()]
            })

            ranking_final = pd.concat([ranking, total], ignore_index=True)

            st.table(ranking_final)

        else:
            st.info("Sem despesas")

    st.stop()

# =========================
# 🔵 GESTÃO
# =========================
st.subheader(f"➕ Novo registo ({modo})")

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

for _, row in df[df["Pessoa"] == modo].iterrows():

    c1, c2, c3, c4, c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(row["Valor"])

    if c5.button("❌", key=f"del_{row['sheet_row']}"):
        sheet.delete_rows(row["sheet_row"])
        st.cache_data.clear()
        st.success("Eliminado")
        st.rerun()
