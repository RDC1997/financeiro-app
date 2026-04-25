import streamlit as st
import pandas as pd
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(page_title="Rubi&Gabi Finance", layout="wide")
st.title("💰 Controlo Financeiro")

# =========================
# GOOGLE SHEETS
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

    sheet = client.open_by_key(
        "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
    ).sheet1

    cat_sheet = client.open_by_key(
        "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
    ).worksheet("Categorias")

    # ✅ NOVO: METAS
    goals_sheet = client.open_by_key(
        "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
    ).worksheet("Metas")

except Exception as e:
    st.error(f"❌ Erro ao ligar ao Google Sheets: {e}")
    st.stop()

# =========================
# CATEGORIAS
# =========================
@st.cache_data(ttl=10)
def load_categories():
    data = cat_sheet.get_all_values()

    if len(data) < 2:
        return []

    return [row[0] for row in data[1:] if row[0].strip() != ""]

def add_category(cat):
    cat_sheet.append_row([cat])

def delete_category(cat):
    data = cat_sheet.get_all_values()

    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == cat:
            cat_sheet.delete_rows(i + 1)
            break

categories = load_categories()

# =========================
# METAS (NOVO)
# =========================
@st.cache_data(ttl=10)
def load_goals():
    data = goals_sheet.get_all_values()

    if len(data) < 2:
        return pd.DataFrame(columns=["Nome","Objetivo","Atual"])

    df = pd.DataFrame(data[1:], columns=data[0])
    df["Objetivo"] = pd.to_numeric(df["Objetivo"], errors="coerce").fillna(0)
    df["Atual"] = pd.to_numeric(df["Atual"], errors="coerce").fillna(0)

    return df

goals = load_goals()

# =========================
# DATA
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()

    expected_cols = [
        "Pessoa",
        "Tipo",
        "Categoria",
        "Descrição",
        "Valor",
        "Data"
    ]

    if not raw or len(raw) < 2:
        return pd.DataFrame(columns=expected_cols)

    headers = [h.strip() for h in raw[0]]
    df = pd.DataFrame(raw[1:], columns=headers)

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    df["Pessoa"] = df["Pessoa"].astype(str).str.strip()
    df["Tipo"] = df["Tipo"].astype(str).str.strip()
    df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df["Descrição"] = df["Descrição"].astype(str).fillna("")
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date

    df["sheet_row"] = df.index + 2

    return df


df = load_data()

# =========================
# DELETE
# =========================
def delete_row_safe(row):
    try:
        sheet.delete_rows(int(row))
        return True
    except Exception as e:
        st.error(f"Erro ao eliminar: {e}")
        return False

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## ⚙️ Categorias")

with st.sidebar.expander("➕ Adicionar categoria"):
    nova_cat = st.text_input("Nova categoria")

    if st.button("Adicionar"):
        if nova_cat.strip() != "":
            add_category(nova_cat.strip())
            st.cache_data.clear()
            st.rerun()

with st.sidebar.expander("❌ Remover categoria"):
    if categories:
        cat_del = st.selectbox("Escolhe categoria", categories)

        if st.button("Remover"):
            delete_category(cat_del)
            st.cache_data.clear()
            st.rerun()

# =========================
# MODO
# =========================
modo = st.sidebar.selectbox("Modo", ["Casal", "Ruben", "Gabi", "🎯 Metas"])

avatars = {
    "Ruben": "🤴",
    "Gabi": "👸"
}

# =========================
# 🎯 METAS (CASAL)
# =========================
if modo == "🎯 Metas":

    st.subheader("🎯 Metas Financeiras do Casal")

    st.markdown("### ➕ Criar meta")

    nome = st.text_input("Nome da meta")
    objetivo = st.number_input("Objetivo (€)", min_value=0.0)

    if st.button("Adicionar meta"):
        goals_sheet.append_row([nome, objetivo, 0])
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    st.subheader("📊 Progresso das metas")

    for i, row in goals.iterrows():

        nome = row["Nome"]
        objetivo = float(row["Objetivo"])
        atual = float(row["Atual"])

        percent = (atual / objetivo * 100) if objetivo > 0 else 0
        percent = min(percent, 100)

        if percent <= 25:
            cor = "🔴"
        elif percent <= 50:
            cor = "🟠"
        elif percent <= 75:
            cor = "🟡"
        else:
            cor = "🟢"

        st.markdown(f"### 🎯 {nome}")
        st.write(f"{cor} {percent:.1f}%")

        st.progress(percent / 100)

        col1, col2, col3 = st.columns(3)

        novo_nome = col1.text_input("Nome", nome, key=f"n{i}")
        novo_obj = col2.number_input("Objetivo", value=objetivo, key=f"o{i}")
        novo_atual = col3.number_input("Atual", value=atual, key=f"a{i}")

        if st.button("Atualizar", key=f"u{i}"):

            goals_sheet.update_cell(i+2, 1, novo_nome)
            goals_sheet.update_cell(i+2, 2, novo_obj)
            goals_sheet.update_cell(i+2, 3, novo_atual)

            st.cache_data.clear()
            st.rerun()

        if st.button("🗑 Remover", key=f"d{i}"):

            goals_sheet.delete_rows(i+2)

            st.cache_data.clear()
            st.rerun()

    st.stop()

# =========================
# CASAL
# =========================
if modo == "Casal":

    st.subheader("📊 Visão Geral (Ciclos por salário)")

    def get_last_salary(df, pessoa):
        df_p = df[(df["Pessoa"] == pessoa) & (df["Tipo"] == "Salário")]
        if df_p.empty:
            return None
        return df_p.sort_values("Data", ascending=False).iloc[0]["Data"]

    def filtrar_ciclo(df, pessoa):
        last_salary = get_last_salary(df, pessoa)

        if not last_salary:
            return df[df["Pessoa"] == pessoa]

        return df[(df["Pessoa"] == pessoa) & (df["Data"] >= last_salary)]

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = filtrar_ciclo(df, pessoa)

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        c1, c2 = st.columns(2)

        c1.metric("💰 Receitas", f"€ {receitas['Valor'].sum():.2f}")
        c2.metric("💸 Despesas", f"€ {despesas['Valor'].sum():.2f}")

    st.stop()

# =========================
# INDIVIDUAL
# =========================
st.subheader(f"{avatars[modo]} {modo}")

pessoa = modo

tipo = st.selectbox("Tipo", ["Salário", "Subsídio Alimentação", "Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":

    if categories:
        categoria = st.selectbox("Categoria", categories)
    else:
        categoria = st.text_input("Categoria")

    descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):

    sheet.append_row([
        pessoa,
        tipo,
        categoria,
        descricao,
        float(valor),
        str(data)
    ])

    st.cache_data.clear()
    st.rerun()

# =========================
# ELIMINAR
# =========================
st.markdown("---")
st.subheader("🗑 Eliminar registos")

df_user = df[df["Pessoa"] == modo].sort_values("Data", ascending=False)

for _, row in df_user.iterrows():

    c1, c2, c3, c4, c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(f"€ {row['Valor']:.2f}")

    if c5.button("❌", key=row["sheet_row"]):
        if delete_row_safe(row["sheet_row"]):
            st.cache_data.clear()
            st.rerun()
