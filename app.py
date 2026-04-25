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

    sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").sheet1
    cat_sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").worksheet("Categorias")

    # METAS SHEET (seguro)
    try:
        goal_sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").worksheet("Metas")
    except:
        goal_sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").add_worksheet("Metas", 100, 3)
        goal_sheet.append_row(["Meta","Objetivo","Atual"])

except Exception as e:
    st.error(f"❌ Erro ao ligar ao Google Sheets: {e}")
    st.stop()

# =========================
# CATEGORIAS (SEM PERDER FUNCIONALIDADE)
# =========================
@st.cache_data(ttl=10)
def load_categories():
    data = cat_sheet.get_all_values()
    if len(data) < 2:
        return []
    return [row[0] for row in data[1:] if row[0].strip()]

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
# SIDEBAR CATEGORIAS (MANTIDO)
# =========================
st.sidebar.markdown("## ⚙️ Categorias")

with st.sidebar.expander("➕ Adicionar categoria"):
    new_cat = st.text_input("Nova categoria")
    if st.button("Adicionar categoria"):
        if new_cat.strip():
            add_category(new_cat.strip())
            st.cache_data.clear()
            st.rerun()

with st.sidebar.expander("❌ Remover categoria"):
    if categories:
        cat_del = st.selectbox("Escolhe categoria", categories)
        if st.button("Remover categoria"):
            delete_category(cat_del)
            st.cache_data.clear()
            st.rerun()

with st.sidebar.expander("📋 Ver categorias"):
    st.write(categories)

# =========================
# DATA
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()

    expected_cols = ["Pessoa","Tipo","Categoria","Descrição","Valor","Data"]

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
# METAS (NOVO SISTEMA COMPLETO)
# =========================
def load_goals():
    data = goal_sheet.get_all_records()
    return pd.DataFrame(data)

goals = load_goals()

# =========================
# DELETE SAFE
# =========================
def delete_row_safe(row):
    try:
        sheet.delete_rows(int(row))
        return True
    except Exception as e:
        st.error(f"Erro ao eliminar: {e}")
        return False

# =========================
# MENU
# =========================
modo = st.sidebar.selectbox("Modo", ["Casal 👨‍❤️‍👩", "Ruben 🤴", "Gabi 👸", "Metas 🎯"])

# =========================
# METAS 🎯 (NOVO + VISUAL)
# =========================
if modo == "Metas 🎯":

    st.subheader("🎯 Metas Financeiras")

    with st.expander("➕ Criar meta"):
        nome = st.text_input("Nome da meta")
        objetivo = st.number_input("Objetivo (€)", min_value=0.0)

        if st.button("Criar"):
            goal_sheet.append_row([nome, objetivo, 0])
            st.rerun()

    for i, row in goals.iterrows():

        meta = row["Meta"]
        obj = float(row["Objetivo"])
        atual = float(row["Atual"])

        percent = (atual / obj * 100) if obj > 0 else 0

        # CORES LÓGICAS
        if percent < 25:
            emoji = "🔴"
        elif percent < 50:
            emoji = "🟠"
        elif percent < 75:
            emoji = "🟡"
        else:
            emoji = "🟢"

        st.write(f"## 🎯 {meta}")
        st.progress(min(percent / 100, 1))
        st.write(f"{emoji} {percent:.1f}% — € {atual:.2f} / € {obj:.2f}")

        col1, col2 = st.columns(2)

        add = col1.number_input("Adicionar valor", min_value=0.0, key=f"add_{i}")

        if col1.button("Adicionar", key=f"btn_{i}"):
            goal_sheet.update_cell(i + 2, 3, atual + add)
            st.rerun()

        if col2.button("Eliminar", key=f"del_{i}"):
            goal_sheet.delete_rows(i + 2)
            st.rerun()

    st.stop()

# =========================
# CASAL / RUBEN / GABI
# =========================
avatars = {
    "Ruben 🤴": "🤴",
    "Gabi 👸": "👸",
    "Casal 👨‍❤️‍👩": "👨‍❤️‍👩"
}

st.subheader(f"{avatars.get(modo, '👤')} {modo}")

pessoa = modo.split()[0] if "Casal" not in modo else None

def filtrar(df, pessoa):
    return df[df["Pessoa"] == pessoa] if pessoa else df

df_user = filtrar(df, pessoa)

receitas = df_user[df_user["Tipo"].isin(["Salário","Subsídio Alimentação"])]
despesas = df_user[df_user["Tipo"] == "Despesa"]

st.markdown("### 💰 Receitas")
st.dataframe(receitas)

st.markdown("### 💸 Despesas")
st.dataframe(despesas)

# =========================
# ADICIONAR REGISTO
# =========================
tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox("Categoria", categories if categories else ["Outros"])
    descricao = st.text_input("Descrição")

valor = st.number_input("Valor (€)", min_value=0.0)
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):
    sheet.append_row([
        pessoa if pessoa else "Casal",
        tipo,
        categoria,
        descricao,
        float(valor),
        str(data)
    ])
    st.rerun()

# =========================
# ELIMINAR
# =========================
st.markdown("---")
st.subheader("🗑 Eliminar registos")

for _, row in df_user.sort_values("Data", ascending=False).iterrows():

    c1,c2,c3,c4,c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(f"€ {row['Valor']:.2f}")

    if c5.button("❌", key=row["sheet_row"]):
        delete_row_safe(row["sheet_row"])
        st.rerun()
