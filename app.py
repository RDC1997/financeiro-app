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
    df = pd.DataFrame(data)

    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
        df["Mês"] = pd.to_numeric(df["Mês"], errors="coerce").fillna(0).astype(int)
        df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").fillna(0).astype(int)

    return df


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
# NOVO REGISTO
# =========================
st.subheader("➕ Novo registo")

col1, col2 = st.columns(2)

with col1:
    pessoa = st.selectbox("Pessoa", ["Ruben", "Gabi"])
    tipo = st.selectbox(
        "Tipo",
        ["Salário", "Subsídio Alimentação", "Despesa"]
    )

with col2:
    valor = st.number_input(
        "Valor (€)",
        min_value=0.0,
        step=10.0
    )
    data = st.date_input("Data", datetime.today())

categoria = ""
descricao = ""

with col1:
    if tipo == "Despesa":


# =========================
# ADICIONAR
# =========================
if st.button("Adicionar"):

    if valor <= 0:
        st.error("O valor precisa de ser maior que zero.")
        st.stop()

    if tipo == "Despesa" and categoria == "":
        st.error("Seleciona uma categoria.")
        st.stop()

    if categoria == "Outros" and descricao.strip() == "":
        st.error("Preenche a descrição.")
        st.stop()

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
    st.success("Guardado com sucesso ☁️")
    st.rerun()


# =========================
# LOAD DATA
# =========================
df = load_data()

if not df.empty:

    # =========================
    # FILTRO MÊS / ANO
    # =========================
    st.subheader("📅 Filtro")

    col_f1, col_f2 = st.columns(2)

    meses = sorted(df["Mês"].unique())
    anos = sorted(df["Ano"].unique())

    with col_f1:
        mes_filtro = st.selectbox("Mês", meses)

    with col_f2:
        ano_filtro = st.selectbox("Ano", anos)

    df = df[
        (df["Mês"] == mes_filtro) &
        (df["Ano"] == ano_filtro)
    ]


# =========================
# DASHBOARD
# =========================
if not df.empty:

    st.subheader("📊 Visão Geral")

    receitas = df[
        df["Tipo"].isin(["Salário", "Subsídio Alimentação"])
    ]["Valor"].sum()

    despesas = df[
        df["Tipo"] == "Despesa"
    ]["Valor"].sum()

    saldo = receitas - despesas

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Receitas", f"€ {receitas:.2f}")

    with c2:
        st.metric("Despesas", f"€ {despesas:.2f}")

    with c3:
        st.metric("Saldo", f"€ {saldo:.2f}")


    # =========================
    # ALERTAS
    # =========================
    if despesas > receitas:
        st.warning("⚠️ As despesas ultrapassaram as receitas este mês.")


    # =========================
    # DESPESAS POR CATEGORIA
    # =========================
    despesas_df = df[df["Tipo"] == "Despesa"]

    if not despesas_df.empty:
        st.subheader("🧾 Despesas por Categoria")

        categoria_total = despesas_df.groupby("Categoria")["Valor"] \
            .sum() \
            .reset_index()

        fig_cat = px.pie(
            categoria_total,
            names="Categoria",
            values="Valor"
        )

        st.plotly_chart(fig_cat, use_container_width=True)

        top = categoria_total.sort_values(
            "Valor",
            ascending=False
        ).iloc[0]

        st.info(
            f"Maior gasto: {top['Categoria']} → € {top['Valor']:.2f}"
        )


    # =========================
    # RUBEN VS GABI
    # =========================
    st.subheader("⚖️ Ruben vs Gabi")

    fig = px.bar(
        df.groupby("Pessoa")["Valor"].sum().reset_index(),
        x="Pessoa",
        y="Valor",
        text="Valor"
    )

    st.plotly_chart(fig, use_container_width=True)


    # =========================
    # META FINANCEIRA
    # =========================
    st.subheader("🎯 Meta Financeira")

    meta = 10000
    progresso = max(0, min(saldo / meta, 1.0))

    st.progress(progresso)
    st.write(f"Objetivo: € {meta:.2f}")
    st.write(f"Atual: € {saldo:.2f}")


    # =========================
    # BACKUP CSV
    # =========================
    st.subheader("⬇️ Backup")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Exportar CSV",
        data=csv,
        file_name="backup_financas.csv",
        mime="text/csv"
    )

else:
    st.info("Sem dados ainda.")
