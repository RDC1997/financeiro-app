import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import time
from io import BytesIO

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(
    page_title="Rubi&Gabi", 
    layout="wide",
    page_icon="💰"
)
st.title("💰 Gestão Financeira 💰")

# =========================
# SESSION STATE
# =========================
if 'inputs' not in st.session_state:
    st.session_state.inputs = {'valor': 0.0,'descricao': '','categoria': ''}

if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = None

# =========================
# HELPERS
# =========================
def refresh():
    st.cache_data.clear()
    load_data.clear()
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

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=scope
)
client = gspread.authorize(creds)

SHEET_ID = "1-kZgk9Xw2fmMkswPJJVlL3eiuMF9g8nJuIJo6UX9XME"
sheet = client.open_by_key(SHEET_ID).sheet1

# =========================
# DATA
# =========================
@st.cache_data(ttl=300)
def load_data():
    raw = sheet.get_all_values()
    if len(raw) < 2:
        return pd.DataFrame(columns=["ID","Pessoa","Tipo","Categoria","Descrição","Valor","Data"])

    df = pd.DataFrame(raw[1:], columns=raw[0])
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    return df

df = load_data()

# =========================
# MENU (SEM INÍCIO)
# =========================
modo = st.sidebar.selectbox(
    "Modo",
    ["Casal 👨‍❤️‍👩","Ruben 🤴","Gabi 👸"]
)

# =========================
# CASAL
# =========================
if modo == "Casal 👨‍❤️‍👩":

    st.subheader("👨‍❤️‍👩 Visão do Casal")

    receitas = df[df["Tipo"].isin(["Salário","Subsídio Alimentação"])]
    despesas = df[df["Tipo"] == "Despesa"]

    total_r = receitas["Valor"].sum()
    total_d = despesas["Valor"].sum()
    saldo = total_r - total_d

    c1,c2,c3 = st.columns(3)
    c1.metric("Receitas", f"{total_r:.2f}€")
    c2.metric("Despesas", f"{total_d:.2f}€")
    c3.metric("Saldo", f"{saldo:.2f}€")

    st.markdown("---")

    col1,col2 = st.columns(2)

    with col1:
        st.markdown("### 💰 Receitas")
        if not receitas.empty:
            st.dataframe(receitas.drop(columns=["ID"], errors="ignore"), use_container_width=True)
        else:
            st.info("Sem receitas")

    with col2:
        st.markdown("### 💸 Despesas")
        if not despesas.empty:
            st.dataframe(despesas.drop(columns=["ID"], errors="ignore"), use_container_width=True)
        else:
            st.info("Sem despesas")

    st.stop()

# =========================
# INDIVIDUAL
# =========================
pessoa = modo.split()[0]

st.subheader(pessoa)

tipo = st.selectbox("Tipo", ["Salário","Subsídio Alimentação","Despesa"])
valor = st.number_input("Valor", min_value=0.0)
data = st.date_input("Data", datetime.today())

if st.button("Adicionar"):
    sheet.append_row([
        generate_id(),
        pessoa,
        tipo,
        "",
        "",
        valor,
        str(data)
    ])
    refresh()
