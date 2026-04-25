import streamlit as st
import pandas as pd
from datetime import datetime
import time
import uuid
import plotly.express as px

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="Rubi&Gabi Finance 2.0", layout="wide")
st.title("💰 Controlo Financeiro 2.0")

# =========================
# HELPERS
# =========================
def safe_sleep():
    time.sleep(0.3)

def refresh():
    st.cache_data.clear()
    st.rerun()

def generate_id():
    return str(uuid.uuid4())

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

    SHEET_ID = "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"

    sheet = client.open_by_key(SHEET_ID).sheet1
    cat_sheet = client.open_by_key(SHEET_ID).worksheet("Categorias")

    try:
        goal_sheet = client.open_by_key(SHEET_ID).worksheet("Metas")
    except:
        goal_sheet = client.open_by_key(SHEET_ID).add_worksheet("Metas", 100, 3)
        goal_sheet.append_row(["Meta", "Objetivo", "Atual"])

except Exception as e:
    st.error(f"Erro Google Sheets: {e}")
    st.stop()

# =========================
# MIGRAÇÃO (VERSÃO 2 - ID SYSTEM)
# =========================
def migrate_if_needed():
    data = sheet.get_all_values()

    if not data:
        sheet.append_row(["ID","Pessoa","Tipo","Categoria","Descrição","Valor","Data"])
        return

    headers = data[0]

    if "ID" not in headers:
        st.warning("🔄 A migrar base de dados para versão 2.0...")

        new_data = [["ID","Pessoa","Tipo","Categoria","Descrição","Valor","Data"]]

        for row in data[1:]:
            new_data.append([
                generate_id(),
                *row
            ])

        sheet.clear()
        sheet.update(new_data)

        st.success("Migração concluída!")

migrate_if_needed()

# =========================
# CATEGORIAS
# =========================
@st.cache_data(ttl=30)
def load_categories():
    data = cat_sheet.get_all_values()
    return [r[0] for r in data[1:] if len(r) > 0]

def add_category(cat):
    safe_sleep()
    cat_sheet.append_row([cat])

def delete_category(cat):
    safe_sleep()
    data = cat_sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == cat:
            cat_sheet.delete_rows(i + 1)
            break

categories = load_categories()

# =========================
# DATA LOAD
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()
    cols = ["ID","Pessoa","Tipo","Categoria","Descrição","Valor","Data"]

    if len(raw) < 2:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(raw[1:], columns=raw[0])

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date

    return df

# =========================
# METAS
# =========================
@st.cache_data(ttl=30)
def load_goals():
    raw = goal_sheet.get_all_values()

    if len(raw) < 2:
        return pd.DataFrame(columns=["Meta","Objetivo","Atual"])

    df = pd.DataFrame(raw[1:], columns=raw[0])
    df["Objetivo"] = pd.to_numeric(df["Objetivo"], errors="coerce").fillna(0)
    df["Atual"] = pd.to_numeric(df["Atual"], errors="coerce").fillna(0)

    df["row"] = df.index + 2
    return df

# =========================
# DELETE SAFE (BY ID)
# =========================
def delete_by_id(record_id):
    data = sheet.get_all_values()

    headers = data[0]
    id_index = headers.index("ID")

    for i, row in enumerate(data[1:], start=2):
        if row[id_index] == record_id:
            sheet.delete_rows(i)
            return True

    return False

# =========================
# MENU
# =========================
modo = st.sidebar.selectbox(
    "Modo",
    ["Dashboard 📊","Casal 👨‍❤️‍👩","Ruben 🤴","Gabi 👸","Metas 🎯"]
)

avatars = {"Ruben":"🤴","Gabi":"👸"}

df = load_data()

# =========================
# DASHBOARD
# =========================
if modo == "Dashboard 📊":

    st.subheader("📊 Visão Geral")

    total_receitas = df[df["Tipo"] != "Despesa"]["Valor"].sum()
    total_despesas = df[df["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = total_receitas - total_despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Receitas", f"{total_receitas:.2f} €")
    c2.metric("💸 Despesas", f"{total_despesas:.2f} €")
    c3.metric("📊 Saldo", f"{saldo:.2f} €")

    st.markdown("---")

    chart = df[df["Tipo"] == "Despesa"]
    fig = px.bar(chart, x="Categoria", y="Valor", color="Pessoa", title="Despesas por Categoria")
    st.plotly_chart(fig, use_container_width=True)

    st.stop()

# =========================
# METAS
# =========================
if modo == "Metas 🎯":

    st.subheader("🎯 Metas")

    goals = load_goals()

    with st.expander("➕ Nova meta"):
        nome = st.text_input("Meta")
        obj = st.number_input("Objetivo (€)", min_value=0.0)

        if st.button("Criar"):
            goal_sheet.append_row([nome,obj,0])
            refresh()

    for _, row in goals.iterrows():

        meta = row["Meta"]
        obj = float(row["Objetivo"])
        atual = float(row["Atual"])
        r = int(row["row"])

        percent = (atual/obj*100) if obj else 0

        st.write(f"### 🎯 {meta}")
        st.progress(min(percent/100,1))
        st.write(f"{percent:.1f}% — {atual:.2f}/{obj:.2f}")

        c1, c2 = st.columns(2)

        add = c1.number_input("Adicionar", min_value=0.0, key=f"a{r}")

        if c1.button("OK", key=f"b{r}"):
            goal_sheet.update_cell(r,3,atual+add)
            refresh()

        if c2.button("🗑", key=f"d{r}"):
            goal_sheet.delete_rows(r)
            refresh()

    st.stop()

# =========================
# CASAL
# =========================
if modo == "Casal 👨‍❤️‍👩":

    st.subheader("👨‍❤️‍👩 Casal")

    for p in ["Ruben","Gabi"]:

        st.markdown(f"## {avatars[p]} {p}")

        df_p = df[df["Pessoa"] == p]

        st.write("### Despesas")
        st.dataframe(df_p[df_p["Tipo"]=="Despesa"])

        st.write(f"Total: {df_p[df_p['Tipo']=='Despesa']['Valor'].sum():.2f} €")

    st.stop()

# =========================
# INDIVIDUAL
# =========================
pessoa = modo.split()[0]

st.subheader(f"{avatars.get(pessoa,'👤')} {pessoa}")

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
        generate_id(),
        pessoa,
        tipo,
        categoria,
        descricao,
        float(valor),
        str(data)
    ])
    refresh()

# =========================
# DELETE
# =========================
st.markdown("---")
st.subheader("🗑 Registos")

df_user = df[df["Pessoa"] == pessoa]

for _, row in df_user.sort_values("Data", ascending=False).iterrows():

    c1,c2,c3,c4,c5 = st.columns([2,3,2,2,1])

    c1.write(row["Pessoa"])
    c2.write(row["Tipo"])
    c3.write(row["Categoria"])
    c4.write(f"{row['Valor']:.2f} €")

    if c5.button("❌", key=row["ID"]):
        delete_by_id(row["ID"])
        refresh()
