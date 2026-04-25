import streamlit as st
import pandas as pd
import plotly.express as px
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
# LOAD DATA
# =========================
def load_data():
    raw = sheet.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(raw[1:], columns=raw[0])
    df.columns = df.columns.str.strip()

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Mês"] = pd.to_numeric(df["Mês"], errors="coerce").fillna(0).astype(int)
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").fillna(0).astype(int)

    return df

# =========================
# SAVE DATA
# =========================
def guardar(d):
    sheet.append_row([
        d["Pessoa"],
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
# FILTRO SIMPLES (MOBILE FRIENDLY)
# =========================
st.sidebar.header("🔍 Filtros")

pessoa_f = st.sidebar.selectbox("Pessoa", ["Todos", "Ruben", "Gabi"])

df_view = df.copy()

if not df_view.empty:
    if pessoa_f != "Todos":
        df_view = df_view[df_view["Pessoa"] == pessoa_f]

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
    st.success("Guardado")
    st.rerun()

# =========================
# DASHBOARD LIMPO (VERSÃO 4)
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

    # =========================
    # ONDE O DINHEIRO VAI (MOBILE CLEAN)
    # =========================
    st.subheader("📉 Onde gastas mais")

    cat = df_view[df_view["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()

    if not cat.empty:
        fig = px.bar(
            cat.sort_values("Valor", ascending=False),
            x="Categoria",
            y="Valor"
        )

        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="",
            yaxis_title=""
        )

        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # EVOLUÇÃO FINANCEIRA (SIMPLIFICADA MOBILE)
    # =========================
    st.subheader("📈 Evolução do saldo")

    temp = df_view.copy()

    temp["Movimento"] = temp.apply(
        lambda x: x["Valor"] if x["Tipo"] != "Despesa" else -x["Valor"],
        axis=1
    )

    temp = temp.sort_values("Data")
    temp["Saldo"] = temp["Movimento"].cumsum()

    fig2 = px.line(
        temp,
        x="Data",
        y="Saldo"
    )

    fig2.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="",
        yaxis_title=""
    )

    fig2.update_xaxes(showgrid=False)
    fig2.update_yaxes(showgrid=False)

    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Sem dados ainda")
