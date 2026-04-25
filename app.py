import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(page_title="Rubi&Gabi", layout="wide")
st.title("💰 Rubi&Gabi - Controlo Financeiro")

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

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

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
        str(d["Data"]),
        int(d["Mês"]),
        int(d["Ano"])
    ])

df = load_data()

# =========================
# FILTROS
# =========================
st.sidebar.header("🔍 Filtros")

pessoa_f = st.sidebar.selectbox("Pessoa", ["Todos", "Ruben", "Gabi"])

if not df.empty:
    meses = sorted(df["Mês"].unique())
    anos = sorted(df["Ano"].unique())

    mes_f = st.sidebar.selectbox("Mês", ["Todos"] + list(meses))
    ano_f = st.sidebar.selectbox("Ano", ["Todos"] + list(anos))
else:
    mes_f = "Todos"
    ano_f = "Todos"

df_view = df.copy()

if pessoa_f != "Todos":
    df_view = df_view[df_view["Pessoa"] == pessoa_f]

if mes_f != "Todos":
    df_view = df_view[df_view["Mês"] == mes_f]

if ano_f != "Todos":
    df_view = df_view[df_view["Ano"] == ano_f]

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
# DASHBOARD
# =========================
if not df_view.empty:

    receitas = df_view[df_view["Tipo"].isin(["Salário","Subsídio Alimentação"])]["Valor"].sum()
    despesas = df_view[df_view["Tipo"]=="Despesa"]["Valor"].sum()
    saldo = receitas - despesas

    c1,c2,c3 = st.columns(3)
    c1.metric("Receitas", f"€ {receitas:.2f}")
    c2.metric("Despesas", f"€ {despesas:.2f}")
    c3.metric("Saldo", f"€ {saldo:.2f}")

    # =========================
    # ALERTAS INTELIGENTES
    # =========================
    st.subheader("⚠️ Alertas")

    if despesas > receitas:
        st.error("Estás a gastar mais do que recebes!")

    if receitas > 0 and despesas / receitas > 0.8:
        st.warning("Estás a aproximar-te do limite saudável de gastos")

    media_despesas = df_view[df_view["Tipo"]=="Despesa"]["Valor"].mean()
    if despesas > media_despesas * 1.5:
        st.warning("Gastos acima da tua média habitual")

    # =========================
    # EVOLUÇÃO SALDO (REAL)
    # =========================
    st.subheader("📈 Evolução financeira")

    temp = df_view.copy()

    temp["Movimento"] = temp.apply(
        lambda x: x["Valor"] if x["Tipo"] != "Despesa" else -x["Valor"],
        axis=1
    )

    temp = temp.sort_values("Data")
    temp["Saldo acumulado"] = temp["Movimento"].cumsum()

    st.plotly_chart(
        px.line(temp, x="Data", y="Saldo acumulado"),
        use_container_width=True
    )

    # =========================
    # TENDÊNCIA (PREVISÃO SIMPLES)
    # =========================
    st.subheader("🔮 Tendência financeira")

    if len(temp) > 3:
        x = np.arange(len(temp))
        y = temp["Saldo acumulado"].values

        coef = np.polyfit(x, y, 1)
        trend = np.poly1d(coef)

        future = trend(len(temp) + 5)

        st.info(f"Previsão simples de tendência: € {future:.2f}")

    # =========================
    # CATEGORIAS
    # =========================
    st.subheader("🔥 Onde gastas mais")

    cat = df_view[df_view["Tipo"]=="Despesa"].groupby("Categoria")["Valor"].sum().reset_index()

    if not cat.empty:
        st.plotly_chart(
            px.bar(cat.sort_values("Valor", ascending=False), x="Categoria", y="Valor"),
            use_container_width=True
        )

    # =========================
    # METAS INTELIGENTES
    # =========================
    st.subheader("🎯 Metas")

    if "metas" not in st.session_state:
        st.session_state.metas = [
            {"nome":"Casa","valor":10000},
            {"nome":"Carro","valor":5000},
            {"nome":"Poupança","valor":2000}
        ]

    novas = []

    for i,m in enumerate(st.session_state.metas):

        col1,col2 = st.columns(2)

        with col1:
            nome = st.text_input("", value=m["nome"], key=f"mn_{i}", label_visibility="collapsed")

        with col2:
            val = st.number_input("Meta", value=float(m["valor"]), key=f"mv_{i}")

        progresso = max(0, min(saldo / val, 1)) if val > 0 else 0

        if progresso < 0.3:
            st.error(f"{nome} - Fraco progresso")
        elif progresso < 0.7:
            st.warning(f"{nome} - Médio progresso")
        else:
            st.success(f"{nome} - Bom progresso")

        st.progress(progresso)

        novas.append({"nome":nome,"valor":val})

    st.session_state.metas = novas

    if st.button("➕ Nova meta"):
        st.session_state.metas.append({"nome":"Nova meta","valor":1000})
        st.rerun()

else:
    st.info("Sem dados")
