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
# LOAD DATA (ROBUSTO)
# =========================
def load_data():
    raw = sheet.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    headers = [h.strip() for h in raw[0]]
    df = pd.DataFrame(raw[1:], columns=headers)

    df.columns = df.columns.str.strip().str.replace("\xa0", "", regex=True)

    required = ["Valor", "Mês", "Ano"]
    for col in required:
        if col not in df.columns:
            st.error(f"Coluna em falta no Google Sheets: {col}")
            return pd.DataFrame()

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
# LOAD
# =========================
df = load_data()

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
            ["Renda","Água","Luz","Vodafone","Alimentação","Gasolina","Outros"]
        )

        if categoria == "Outros":
            descricao = st.text_input("Descrição")

with col2:
    valor = st.number_input("Valor (€)", min_value=0.0, step=10.0)
    data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):

    if valor <= 0:
        st.error("Valor inválido")
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
    st.success("Guardado")
    st.rerun()

# =========================
# DELETE + EDIT
# =========================
st.subheader("🗑️ Eliminar / ✏️ Editar registos")

if not df.empty:

    raw = sheet.get_all_values()
    rows = raw[1:]

    data_list = []

    for i, r in enumerate(rows, start=2):
        if len(r) >= 6:
            data_list.append({
                "linha": i,
                "Pessoa": r[0],
                "Tipo": r[1],
                "Categoria": r[2],
                "Descrição": r[3],
                "Valor": float(r[4]) if r[4] else 0,
                "Data": r[5]
            })

    df_m = pd.DataFrame(data_list)

    escolha = st.selectbox(
        "Seleciona registo",
        df_m.index,
        format_func=lambda x:
            f"{df_m.loc[x,'Pessoa']} | {df_m.loc[x,'Tipo']} | €{df_m.loc[x,'Valor']}"
    )

    linha = int(df_m.loc[escolha, "linha"])

    # =========================
    # DELETE COM CONFIRMAÇÃO
    # =========================
    confirm = st.checkbox("Confirmo que quero apagar este registo")

    if confirm and st.button("🗑️ Apagar"):
        sheet.delete_rows(linha)
        st.success("Eliminado")
        st.rerun()

    # =========================
    # EDITAR REGISTO
    # =========================
    st.markdown("---")
    st.subheader("✏️ Editar registo")

    row = df_m.loc[escolha]

    pessoa_e = st.selectbox("Pessoa", ["Ruben","Gabi"], index=["Ruben","Gabi"].index(row["Pessoa"]))
    tipo_e = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"], index=["Salário","Subsídio Alimentação","Despesa"].index(row["Tipo"]))

    categoria_e = row["Categoria"]
    descricao_e = row["Descrição"]

    if tipo_e == "Despesa":
        categoria_e = st.selectbox("Categoria",
            ["Renda","Água","Luz","Vodafone","Alimentação","Gasolina","Outros"])

        if categoria_e == "Outros":
            descricao_e = st.text_input("Descrição", value=row["Descrição"])

    valor_e = st.number_input("Valor", value=float(row["Valor"]))

    if st.button("💾 Guardar alterações"):
        sheet.update(f"A{linha}:H{linha}", [[
            pessoa_e,
            tipo_e,
            categoria_e,
            descricao_e,
            valor_e,
            row["Data"],
            row.get("Mês",0),
            row.get("Ano",0)
        ]])
        st.success("Atualizado")
        st.rerun()

else:
    st.info("Sem dados")

# =========================
# FILTRO
# =========================
if not df.empty:

    st.subheader("📅 Filtro")

    col1, col2 = st.columns(2)

    meses = sorted(df["Mês"].unique())
    anos = sorted(df["Ano"].unique())

    mes = st.selectbox("Mês", meses)
    ano = st.selectbox("Ano", anos)

    df = df[(df["Mês"] == mes) & (df["Ano"] == ano)]

# =========================
# DASHBOARD
# =========================
if not df.empty:

    receitas = df[df["Tipo"].isin(["Salário","Subsídio Alimentação"])]
    receitas = receitas["Valor"].sum()

    despesas = df[df["Tipo"] == "Despesa"]["Valor"].sum()

    saldo = receitas - despesas

    c1,c2,c3 = st.columns(3)

    c1.metric("Receitas", f"€ {receitas:.2f}")
    c2.metric("Despesas", f"€ {despesas:.2f}")
    c3.metric("Saldo", f"€ {saldo:.2f}")

    st.subheader("📊 Categorias")
    cat = df[df["Tipo"]=="Despesa"].groupby("Categoria")["Valor"].sum().reset_index()

    if not cat.empty:
        st.plotly_chart(px.bar(cat,x="Categoria",y="Valor"),use_container_width=True)

    # =========================
    # META MULTIPLA
    # =========================
    st.subheader("🎯 Metas")

    if "metas" not in st.session_state:
        st.session_state.metas = {
            "Casa":10000,
            "Carro":5000,
            "Poupança":2000
        }

    for k in st.session_state.metas:
        st.session_state.metas[k] = st.number_input(k, value=float(st.session_state.metas[k]))
        prog = max(0,min(saldo/st.session_state.metas[k],1)) if st.session_state.metas[k]>0 else 0
        st.progress(prog)

    # =========================
    # BACKUP
    # =========================
    st.download_button("Backup CSV", df.to_csv(index=False).encode(), "backup.csv")

else:
    st.info("Sem dados")
