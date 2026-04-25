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
modo = st.sidebar.selectbox("Modo", ["Casal", "Ruben", "Gabi"], key="modo")

# =========================
# CASAL (VISUALIZAÇÃO)
# =========================
if modo == "Casal":

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_pessoa = df[df["Pessoa"] == pessoa]

        receitas = df_pessoa[df_pessoa["Tipo"].isin(["Salário", "Subsídio Alimentação"])]
        despesas = df_pessoa[df_pessoa["Tipo"] == "Despesa"]

        st.markdown("### 💰 Receitas")

        if not receitas.empty:
            tabela_r = receitas[["Tipo", "Valor"]].groupby("Tipo").sum().reset_index()
            tabela_r["Valor"] = tabela_r["Valor"].apply(lambda x: f"{x:.0f}")
            st.table(tabela_r)
        else:
            st.info("Sem receitas")

        st.markdown("### 💸 Despesas")

        if not despesas.empty:
            despesas = despesas.copy()

            # 🔥 FIX IMPORTANTE: juntar categoria + descrição
            despesas["Categoria"] = despesas.apply(
                lambda row: f"{icons.get(row['Categoria'], '')} {row['Categoria']} - {row['Descrição']}" 
                if row["Categoria"] == "Outros"
                else f"{icons.get(row['Categoria'], '')} {row['Categoria']}",
                axis=1
            )

            tabela_d = despesas[["Categoria", "Valor"]].groupby("Categoria").sum().reset_index()
            tabela_d["Valor"] = tabela_d["Valor"].apply(lambda x: f"{x:.0f}")

            st.table(tabela_d)

        else:
            st.info("Sem despesas")

        st.markdown("---")

    st.stop()

# =========================
# GESTÃO
# =========================
st.subheader("➕ Novo registo")

pessoa = modo

tipo = st.selectbox("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"], key="tipo_add")

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox(
        "Categoria",
        list(icons.keys()),
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

    st.cache_data.clear()
    st.success("Adicionado com sucesso")
    st.rerun()
