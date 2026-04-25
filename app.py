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
# GOOGLE SHEETS (FIX DEFINITIVO)
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

# 🔥 FIX IMPORTANTE: open_by_key (mais estável)
sheet = client.open_by_key(
    "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
).sheet1

# =========================
# LOAD DATA (ROBUSTO)
# =========================
def normalize_person(x):
    x = str(x).strip().lower()
    if x == "ruben":
        return "Ruben"
    if x == "gabi":
        return "Gabi"
    return x.capitalize()

def load_data():
    raw = sheet.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(raw[1:], columns=raw[0])
    df.columns = df.columns.str.strip()

    df["Pessoa"] = df["Pessoa"].apply(normalize_person)
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

df = load_data()

# =========================
# MODO
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
# NOVO REGISTO (BLOQUEADO POR MODO)
# =========================
if modo != "Casal":

    st.subheader("➕ Novo registo")

    col1, col2 = st.columns(2)

    with col1:

        # 🔥 FIX: pessoa bloqueada automaticamente
        pessoa = modo

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
            "Data": data
        })
        st.success("Adicionado com sucesso")
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

    st.markdown("---")

    # =========================
    # GASTOS POR CATEGORIA
    # =========================
    st.subheader("📉 Gastos")

    gastos = df_view[df_view["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()

    if not gastos.empty:
        for _, row in gastos.iterrows():
            st.write(f"💳 {row['Categoria']} → € {row['Valor']:.2f}")

    st.markdown("---")

    # =========================
    # ELIMINAR (SÓ R E G)
    # =========================
    if modo != "Casal":

        st.subheader("🗑️ Eliminar registo")

        raw = sheet.get_all_values()
        rows = raw[1:]

        data = []
        for i, r in enumerate(rows, start=2):
            if len(r) >= 5:
                data.append({
                    "linha": i,
                    "Pessoa": r[0],
                    "Valor": r[4]
                })

        df_del = pd.DataFrame(data)

        if not df_del.empty:

            idx = st.selectbox("Seleciona registo", df_del.index)
            linha = int(df_del.loc[idx, "linha"])

            confirmar = st.checkbox("Confirmo eliminação")

            if confirmar:
                if st.button("Eliminar"):
                    sheet.delete_rows(linha)
                    st.success("Eliminado")
                    st.rerun()

else:
    st.info("Sem dados ainda")
