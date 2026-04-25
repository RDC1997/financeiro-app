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
# 🔀 MODO DE VISÃO (CASAL / INDIVIDUAL)
# =========================
st.sidebar.header("👁️ Modo de visualização")

modo = st.sidebar.selectbox(
    "Escolhe modo",
    ["Casal (Tudo)", "Ruben", "Gabi"]
)

# FILTRO BASE
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
    st.success("Guardado")
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
    c1.metric("💰 Receitas", f"€ {receitas:.2f}")
    c2.metric("💸 Despesas", f"€ {despesas:.2f}")
    c3.metric("⚖️ Saldo", f"€ {saldo:.2f}")

    # ALERTA SIMPLES
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
    st.subheader("📉 Onde o dinheiro vai")

    gastos = df_view[df_view["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()
    gastos = gastos.sort_values("Valor", ascending=False)

    if not gastos.empty:
        for _, row in gastos.iterrows():
            st.write(f"💳 **{row['Categoria']}** → € {row['Valor']:.2f}")

    st.markdown("---")

    # =========================
    # POR PESSOA (SÓ NO MODO CASAL)
    # =========================
    if modo == "Casal (Tudo)":
        st.subheader("👤 Gastos por pessoa")

        por_pessoa = df_view.groupby("Pessoa")["Valor"].sum().reset_index()

        for _, row in por_pessoa.iterrows():
            st.write(f"👤 **{row['Pessoa']}** → € {row['Valor']:.2f}")

    st.markdown("---")

    # =========================
    # EDITAR / ELIMINAR
    # =========================
    st.subheader("✏️ Editar / Eliminar")

    raw = sheet.get_all_values()
    headers = raw[0]
    rows = raw[1:]

    data = []
    for i, r in enumerate(rows, start=2):
        if len(r) >= 6:
            data.append({
                "linha": i,
                "Pessoa": r[0],
                "Tipo": r[1],
                "Categoria": r[2],
                "Descrição": r[3],
                "Valor": r[4],
                "Data": r[5]
            })

    df_edit = pd.DataFrame(data)

    if not df_edit.empty:

        idx = st.selectbox("Seleciona registo", df_edit.index)
        row = df_edit.loc[idx]
        linha = int(row["linha"])

        # ELIMINAR
        st.markdown("### 🗑️ Eliminar")
        if st.checkbox("Confirmo eliminação"):
            if st.button("Eliminar"):
                sheet.delete_rows(linha)
                st.success("Eliminado")
                st.rerun()

        st.markdown("---")

        # EDITAR
        st.markdown("### ✏️ Editar")

        pessoa_e = st.selectbox(
            "Pessoa",
            ["Ruben","Gabi"],
            index=["Ruben","Gabi"].index(row["Pessoa"]),
            key=f"p_{linha}"
        )

        tipo_e = st.selectbox(
            "Tipo",
            ["Salário","Subsídio Alimentação","Despesa"],
            index=["Salário","Subsídio Alimentação","Despesa"].index(row["Tipo"]),
            key=f"t_{linha}"
        )

        categoria_e = row["Categoria"]
        descricao_e = row["Descrição"]

        if tipo_e == "Despesa":
            categoria_e = st.selectbox(
                "Categoria",
                ["Renda","Água","Luz","Vodafone","Alimentação","Gasolina","Outros"],
                key=f"c_{linha}"
            )

        valor_e = st.number_input(
            "Valor",
            value=float(row["Valor"]),
            key=f"v_{linha}"
        )

        if st.button("Guardar alterações", key=f"s_{linha}"):
            sheet.update(f"A{linha}:H{linha}", [[
                pessoa_e,
                tipo_e,
                categoria_e,
                descricao_e,
                valor_e,
                row["Data"],
                0,
                0
            ]])
            st.success("Atualizado")
            st.rerun()

else:
    st.info("Sem dados ainda")
