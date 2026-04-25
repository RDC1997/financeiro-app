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
    goal_sheet = client.open_by_key("1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME").worksheet("Metas")

except Exception as e:
    st.error(f"❌ Erro ao ligar ao Google Sheets: {e}")
    st.stop()

# =========================
# CATEGORIAS
# =========================
@st.cache_data(ttl=120)
def load_categories():
    data = cat_sheet.get_all_values()
    if len(data) < 2:
        return []
    return [row[0] for row in data[1:] if row[0].strip() != ""]

categories = load_categories()

# =========================
# DATA (OTIMIZADO)
# =========================
@st.cache_data(ttl=120)
def load_data():
    raw = sheet.get_all_values()

    cols = ["Pessoa","Tipo","Categoria","Descrição","Valor","Data"]

    if not raw or len(raw) < 2:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(raw[1:], columns=raw[0])

    for c in cols:
        if c not in df.columns:
            df[c] = ""

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
# METAS (ROBUSTO + SEM BUG DE DELETE)
# =========================
@st.cache_data(ttl=120)
def load_goals():
    raw = goal_sheet.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame(columns=["row","Meta","Objetivo","Atual"])

    df = pd.DataFrame(raw[1:], columns=raw[0])

    for c in ["Meta","Objetivo","Atual"]:
        if c not in df.columns:
            df[c] = 0

    df["Objetivo"] = pd.to_numeric(df["Objetivo"], errors="coerce").fillna(0)
    df["Atual"] = pd.to_numeric(df["Atual"], errors="coerce").fillna(0)

    # 🔥 FIX CRÍTICO: linha real do Google Sheets
    df["row"] = df.index + 2

    return df

# =========================
# SAFE DELETE
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
modo = st.sidebar.selectbox(
    "Modo",
    ["Casal 👨‍❤️‍👩", "Ruben 🤴", "Gabi 👸", "Metas 🎯"]
)

avatars = {
    "Ruben": "🤴",
    "Gabi": "👸",
    "Casal": "👨‍❤️‍👩"
}

# =========================
# METAS (TOTALMENTE ESTÁVEL)
# =========================
if modo == "Metas 🎯":

    st.subheader("🎯 Metas Financeiras")

    goals = load_goals()

    with st.expander("➕ Criar meta"):
        nome = st.text_input("Nome da meta")
        objetivo = st.number_input("Objetivo (€)", min_value=0.0)

        if st.button("Criar"):
            if nome.strip():
                goal_sheet.append_row([nome, objetivo, 0])
                st.cache_data.clear()
                st.rerun()

    for _, row in goals.iterrows():

        meta = row["Meta"]
        obj = float(row["Objetivo"])
        atual = float(row["Atual"])
        r = int(row["row"])

        percent = (atual / obj * 100) if obj > 0 else 0

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

        c1, c2 = st.columns(2)

        add = c1.number_input("Adicionar", min_value=0.0, key=f"add_{r}")

        if c1.button("Adicionar", key=f"btn_{r}"):
            goal_sheet.update_cell(r, 3, atual + add)
            st.cache_data.clear()
            st.rerun()

        if c2.button("Eliminar", key=f"del_{r}"):
            goal_sheet.delete_rows(r)
            st.cache_data.clear()
            st.rerun()

    st.stop()

# =========================
# CASAL (TABELAS COMPLETAS RESTAURADAS)
# =========================
if modo == "Casal 👨‍❤️‍👩":

    st.subheader("📊 CASAL")

    for p in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[p]} {p}")

        df_p = df[df["Pessoa"] == p]

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        st.markdown("### 💰 Receitas")
        st.dataframe(receitas, use_container_width=True)

        st.markdown("### 💸 Despesas")
        st.dataframe(despesas, use_container_width=True)

        st.markdown(f"**Total despesas: € {despesas['Valor'].sum():.2f}**")

    st.stop()

# =========================
# INDIVIDUAL
# =========================
st.subheader(f"{avatars.get(modo.split()[0],'👤')} {modo}")

pessoa = modo.split()[0]

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
# ELIMINAR REGISTOS
# =========================
st.markdown("---")
st.subheader("🗑 Eliminar registos")

df_user = df[df["Pessoa"] == pessoa]

for _, row in df_user.sort_values("Data", ascending=False).iterrows():

    c1, c2, c3, c4, c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(f"€ {row['Valor']:.2f}")

    if c5.button("❌", key=row["sheet_row"]):
        delete_row_safe(row["sheet_row"])
        st.cache_data.clear()
        st.rerun()
