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

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME/edit"
).sheet1

# =========================
# LOAD DATA (CORRIGIDO)
# =========================
def load_data():
    raw = sheet.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(raw[1:], columns=raw[0])
    df.columns = df.columns.str.strip()

    # 🔥 LIMPEZA CRÍTICA (CORREÇÃO DO BUG)
    df["Pessoa"] = df["Pessoa"].astype(str).str.strip().str.capitalize()

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Mês"] = pd.to_numeric(df["Mês"], errors="coerce").fillna(0).astype(int)
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").fillna(0).astype(int)

    return df

# =========================
# SAVE
# =========================
def guardar(d):
    sheet.append_row([
        d["Pessoa"].strip().capitalize(),
        d["Tipo"],
        d["Categoria"],
        d["Descrição"],
        float(d["Valor"]),
        str(d["Data"]),
        int(d["Mês"]),
        int(d["Ano"])
    ])

df = load_data()

# =========================
# MODO VISUALIZAÇÃO (CORRIGIDO)
# =========================
st.sidebar.header("👁️ Modo")

modo = st.sidebar.selectbox(
    "Visualização",
    ["Casal", "Ruben", "Gabi"]
)

df_view = df.copy()

if not df_view.empty:
    if modo == "Ruben":
        df_view = df_view[df_view["Pessoa"] == "Ruben"]
    elif modo == "Gabi":
        df_view = df_view[df_view["Pessoa"] == "Gabi"]

# =========================
# NOVO REGISTO
# =========================
st.subheader("➕ Novo registo")

col1, col2 = st.columns(2)

with col1:
    pessoa = st.selectbox("Pessoa", ["Ruben", "Gabi"])
    tipo = st.selectbox("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"])

    categoria = ""
    descricao = ""

    if tipo == "Despesa":
        categoria = st.selectbox(
            "Categoria",
            ["Renda", "Água", "Luz", "Vodafone", "Alimentação", "Gasolina", "Outros"]
        )

        if categoria == "Outros":
            descricao = st.text_input("Descrição")

with col2:
    valor = st.number_input("Valor (€)", min_value=0.0)
    data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):
    guardar({
        "Pessoa": pessoa,
        "Tipo": tipo,
        "Categoria": categoria,
        "Descrição": descricao,
        "Valor": valor,
        "Data": data,
        "Mês": data.month,
        "Ano": data.year
    })
    st.success(f"Adicionado com sucesso ({pessoa})")
    st.rerun()

# =========================
# RESUMO
# =========================
if not df_view.empty:

    st.subheader("📊 Resumo")

    receitas = df_view[df_view["Tipo"].isin(["Salário","Subsídio Alimentação"])]["Valor"].sum()
    despesas = df_view[df_view["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"€ {receitas:.2f}")
    c2.metric("Despesas", f"€ {despesas:.2f}")
    c3.metric("Saldo", f"€ {saldo:.2f}")

    if saldo < 0:
        st.error("⚠️ Gastos acima dos ganhos")
    elif saldo < 200:
        st.warning("⚠️ Saldo baixo")
    else:
        st.success("✔ Situação estável")

    st.markdown("---")

    # =========================
    # GASTOS POR CATEGORIA
    # =========================
    st.subheader("📉 Gastos principais")

    gastos = df_view[df_view["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()
    gastos = gastos.sort_values("Valor", ascending=False)

    if not gastos.empty:
        for _, row in gastos.iterrows():
            st.write(f"💳 **{row['Categoria']}** → € {row['Valor']:.2f}")

    st.markdown("---")

    # =========================
    # POR PESSOA (CASAL)
    # =========================
    if modo == "Casal":
        st.subheader("👤 Gastos por pessoa")

        por_pessoa = df_view.groupby("Pessoa")["Valor"].sum().reset_index()

        for _, row in por_pessoa.iterrows():
            st.write(f"👤 **{row['Pessoa']}** → € {row['Valor']:.2f}")

else:
    st.info("Sem dados ainda")
