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
# EDITAR / APAGAR
# =========================
st.subheader("🗑️ Editar / Eliminar")

if not df.empty:

    raw = sheet.get_all_values()
    rows = raw[1:]

    data = []
    for i, r in enumerate(rows, start=2):
        data.append({
            "linha": i,
            "Pessoa": r[0],
            "Tipo": r[1],
            "Categoria": r[2],
            "Descrição": r[3],
            "Valor": float(r[4]) if r[4] else 0,
            "Data": r[5]
        })

    df_edit = pd.DataFrame(data)

    idx = st.selectbox("Seleciona registo", df_edit.index)

    row = df_edit.loc[idx]
    linha = int(row["linha"])

    if st.checkbox("Confirmar apagar", key=f"del_{linha}"):
        if st.button("Apagar", key=f"btn_{linha}"):
            sheet.delete_rows(linha)
            st.success("Apagado")
            st.rerun()

    st.markdown("---")
    st.subheader("✏️ Editar")

    pessoa_e = st.selectbox(
        "Pessoa",
        ["Ruben", "Gabi"],
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

        if categoria_e == "Outros":
            descricao_e = st.text_input("Descrição", value=row["Descrição"], key=f"d_{linha}")

    valor_e = st.number_input("Valor", value=float(row["Valor"]), key=f"v_{linha}")

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

# =========================
# DASHBOARD
# =========================
if not df.empty:

    receitas = df[df["Tipo"].isin(["Salário","Subsídio Alimentação"])]["Valor"].sum()
    despesas = df[df["Tipo"]=="Despesa"]["Valor"].sum()
    saldo = receitas - despesas

    c1,c2,c3 = st.columns(3)
    c1.metric("Receitas", f"€ {receitas:.2f}")
    c2.metric("Despesas", f"€ {despesas:.2f}")
    c3.metric("Saldo", f"€ {saldo:.2f}")

    st.subheader("📊 Categorias")
    cat = df[df["Tipo"]=="Despesa"].groupby("Categoria")["Valor"].sum().reset_index()

    if not cat.empty:
        st.plotly_chart(px.bar(cat, x="Categoria", y="Valor"), use_container_width=True)

    # =========================
    # METAS EDITÁVEIS (CORRETO)
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
            nome = st.text_input(
                " ",
                value=m["nome"],
                key=f"mn_{i}",
                label_visibility="collapsed"
            )

        with col2:
            val = st.number_input(
                "Valor",
                value=float(m["valor"]),
                key=f"mv_{i}"
            )

        novas.append({"nome":nome,"valor":val})

    st.session_state.metas = novas

    if st.button("➕ Nova meta"):
        st.session_state.metas.append({"nome":"Nova meta","valor":1000})
        st.rerun()

else:
    st.info("Sem dados")
