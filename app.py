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
# GOOGLE SHEETS (ROBUSTO)
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

    spreadsheet = client.open_by_key(
        "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
    )

    sheet = spreadsheet.get_worksheet(0)

except Exception as e:
    st.error("❌ Erro ao ligar ao Google Sheets")
    st.error(str(e))
    st.stop()

# =========================
# LOAD DATA
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
modo = st.sidebar.selectbox("Modo", ["Casal", "Ruben", "Gabi"])

df_view = df.copy()

if not df_view.empty:
    if modo == "Ruben":
        df_view = df_view[df_view["Pessoa"] == "Ruben"]
    elif modo == "Gabi":
        df_view = df_view[df_view["Pessoa"] == "Gabi"]

# =========================
# ADICIONAR (BLOQUEADO POR MODO)
# =========================
if modo != "Casal":

    st.subheader("➕ Novo registo")

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
    # LISTA DE REGISTOS (EDITAR + ELIMINAR)
    # =========================
    st.subheader("📋 Registos")

    raw = sheet.get_all_values()
    rows = raw[1:]

    data = []
    for i, r in enumerate(rows, start=2):
        if len(r) >= 6:
            data.append({
                "linha": i,
                "Pessoa": r[0],
                "Tipo": r[1],
                "Categoria": r[2],
                "Descricao": r[3],
                "Valor": r[4],
                "Data": r[5]
            })

    df_edit = pd.DataFrame(data)

    if not df_edit.empty:

        idx = st.selectbox(
            "Seleciona registo",
            df_edit.index,
            format_func=lambda i: f"{df_edit.loc[i,'Pessoa']} | {df_edit.loc[i,'Tipo']} | €{df_edit.loc[i,'Valor']}"
        )

        row = df_edit.loc[idx]
        linha = int(row["linha"])

        st.markdown("### ✏️ Editar")

        new_valor = st.number_input("Valor", value=float(row["Valor"]))
        new_tipo = st.selectbox("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"], index=0)
        new_categoria = st.text_input("Categoria", value=row["Categoria"])
        new_descricao = st.text_input("Descrição", value=row["Descricao"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Guardar alterações"):
                sheet.update(f"A{linha}:F{linha}", [[
                    row["Pessoa"],
                    new_tipo,
                    new_categoria,
                    new_descricao,
                    new_valor,
                    row["Data"]
                ]])
                st.success("Atualizado")
                st.rerun()

        with col2:
            confirmar = st.checkbox("Confirmo eliminação")

            if confirmar and st.button("🗑️ Eliminar"):
                sheet.delete_rows(linha)
                st.success("Eliminado")
                st.rerun()

else:
    st.info("Sem dados ainda")
