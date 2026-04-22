import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG APP
# =========================
st.set_page_config(page_title="Rubi&Gabi", layout="wide")
st.title("💰 Rubi&Gabi")

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
# LOAD DATA
# =========================
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# =========================
# SAVE DATA
# =========================
def guardar(d):
    sheet.append_row([
        str(d["Pessoa"]),
        str(d["Tipo"]),
        str(d["Categoria"]),
        str(d["Descrição"]),
        float(d["Valor"]),
        str(d["Data"]),
        int(d["Mês"]),
        int(d["Ano"])
    ])

# =========================
# INPUT
# =========================
st.subheader("➕ Novo registo")

col1, col2 = st.columns(2)

with col1:
    pessoa = st.selectbox("Pessoa", ["Ruben", "Gabi"])
    tipo = st.selectbox("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"])

with col2:
    valor = st.number_input("Valor (€)", min_value=0.0, step=10.0)
    data = st.date_input("Data", datetime.today())

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox(
        "Categoria",
        ["Renda", "Água", "Luz", "Vodafone", "Alimentação", "Gasolina", "Outros"]
    )

    if categoria == "Outros":
        descricao = st.text_input("Descrição")

# =========================
# ADICIONAR
# =========================
if st.button("Adicionar"):

    novo = {
        "Pessoa": pessoa,
        "Tipo": tipo,
        "Categoria": categoria,
        "Descrição": descricao,
        "Valor": valor,
        "Data": data,
        "Mês": data.month,
        "Ano": data.year
    }

    guardar(novo)
    st.success("Guardado ☁️")
    st.rerun()

# =========================
# DADOS
# =========================
df = load_data()

# =========================
# REMOVER (CORRIGIDO 100%)
# =========================
st.subheader("🗑️ Remover movimento")

if not df.empty:

    raw = sheet.get_all_values()
    headers = raw[0]
    rows = raw[1:]

    data = []
    for i, r in enumerate(rows, start=2):  # linha real no Google Sheets
        if len(r) >= 5:
            data.append({
                "Linha": i,
                "Pessoa": r[0],
                "Tipo": r[1],
                "Categoria": r[2],
                "Descricao": r[3],
                "Valor": r[4],
                "Data": r[5] if len(r) > 5 else ""
            })

    df_delete = pd.DataFrame(data)

    escolha = st.selectbox(
        "Seleciona o movimento",
        df_delete.index,
        format_func=lambda i:
            f"{df_delete.loc[i, 'Pessoa']} | {df_delete.loc[i, 'Tipo']} | €{df_delete.loc[i, 'Valor']}"
    )

    linha_real = int(df_delete.loc[escolha, "Linha"])

    st.dataframe(df_delete.drop(columns=["Linha"]), use_container_width=True)

    if st.button("🗑️ Apagar movimento"):

        sheet.delete_rows(linha_real)

        st.success("Movimento apagado 🗑️")
        st.rerun()

else:
    st.info("Sem dados ainda")

# =========================
# DASHBOARD
# =========================
if not df.empty:

    st.subheader("📊 Visão Geral")
    st.metric("Total", f"€ {df['Valor'].sum():.2f}")

    st.subheader("⚖️ Ruben vs Gabi")
    fig = px.bar(df.groupby("Pessoa")["Valor"].sum().reset_index(),
                 x="Pessoa", y="Valor", text="Valor")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📅 Evolução Mensal")
    mensal = df.groupby("Mês")["Valor"].sum().reset_index()

    fig2 = px.line(mensal, x="Mês", y="Valor", markers=True)
    fig2.update_xaxes(dtick=1)

    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Sem dados ainda")
