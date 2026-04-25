import streamlit as st
import pandas as pd
from datetime import datetime
import time
import uuid
import plotly.express as px

import gspread
from google.oauth2.service_account import Credentials

# =========================
# APP
# =========================
st.set_page_config(page_title="Rubi&Gabi Finance PRO 2", layout="wide")
st.title("💰 Controlo Financeiro PRO 2")

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
        goal_sheet.append_row(["Meta","Objetivo","Atual"])

except Exception as e:
    st.error(f"Erro Google Sheets: {e}")
    st.stop()

# =========================
# CATEGORIAS (NÃO ALTERADO)
# =========================
@st.cache_data(ttl=30)
def load_categories():
    data = cat_sheet.get_all_values()
    return [row[0] for row in data[1:] if row[0].strip() != ""]

categories = load_categories()

# =========================
# DATA
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

df = load_data()

# =========================
# MENU
# =========================
modo = st.sidebar.selectbox(
    "Modo",
    ["Casal 👨‍❤️‍👩","Ruben 🤴","Gabi 👸","Metas 🎯"]
)

avatars = {"Ruben":"🤴","Gabi":"👸"}

# =========================
# CASAL PRO 2
# =========================
if modo == "Casal 👨‍❤️‍👩":

    st.subheader("👨‍❤️‍👩 Casal - PRO 2 Inteligente")

    def get_last_salary(df, pessoa):
        df_p = df[(df["Pessoa"] == pessoa) & (df["Tipo"] == "Salário")]
        if df_p.empty:
            return None
        return df_p.sort_values("Data", ascending=False).iloc[0]["Data"]

    def filtrar_ciclo(df, pessoa):
        last_salary = get_last_salary(df, pessoa)

        if last_salary:
            return df[(df["Pessoa"] == pessoa) & (df["Data"] >= last_salary)], "salario"
        else:
            # fallback: último mês
            return df[df["Pessoa"] == pessoa], "mensal"

    total_casal_receitas = 0
    total_casal_despesas = 0

    for pessoa in ["Ruben","Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p, tipo_ciclo = filtrar_ciclo(df, pessoa)

        receitas = df_p[df_p["Tipo"].isin(["Salário","Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        total_receitas = receitas["Valor"].sum()
        total_despesas = despesas["Valor"].sum()
        saldo = total_receitas - total_despesas

        total_casal_receitas += total_receitas
        total_casal_despesas += total_despesas

        # =========================
        # MÉTRICAS PRO
        # =========================
        taxa_poupanca = (saldo / total_receitas * 100) if total_receitas > 0 else 0
        media_despesas = despesas["Valor"].mean() if not despesas.empty else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Receitas", f"{total_receitas:.2f} €")
        c2.metric("💸 Despesas", f"{total_despesas:.2f} €")
        c3.metric("📊 Saldo", f"{saldo:.2f} €")
        c4.metric("📈 Poupança", f"{taxa_poupanca:.1f}%")

        # =========================
        # ALERTAS INTELIGENTES
        # =========================
        if total_despesas > total_receitas:
            st.error("⚠️ Estás a gastar mais do que ganhas neste ciclo!")

        elif taxa_poupanca < 10:
            st.warning("⚠️ Taxa de poupança baixa")

        elif taxa_poupanca > 30:
            st.success("🟢 Excelente controlo financeiro!")

        # =========================
        # GRÁFICO EVOLUTIVO
        # =========================
        if not despesas.empty:
            fig = px.bar(
                despesas,
                x="Categoria",
                y="Valor",
                title=f"Despesas por Categoria - {pessoa}"
            )
            st.plotly_chart(fig, use_container_width=True)

        # =========================
        # TABELAS ORIGINAIS (MANTIDAS)
        # =========================
        with st.expander(f"🔍 Debug - {pessoa}"):
            st.write("Tipo de ciclo:", tipo_ciclo)
            st.write("Último salário:", get_last_salary(df, pessoa))
            st.dataframe(df_p)

        st.markdown("### 💰 Receitas")
        st.dataframe(receitas, use_container_width=True)

        st.markdown("### 💸 Despesas")
        st.dataframe(despesas, use_container_width=True)

    # =========================
    # COMPARAÇÃO CASAL
    # =========================
    st.markdown("---")
    st.subheader("⚖️ Comparação Casal")

    c1, c2 = st.columns(2)
    c1.metric("💰 Receitas Totais", f"{total_casal_receitas:.2f} €")
    c2.metric("💸 Despesas Totais", f"{total_casal_despesas:.2f} €")

    st.stop()

# =========================
# METAS (NÃO ALTERADO)
# =========================
if modo == "Metas 🎯":
    st.subheader("🎯 Metas")
    st.dataframe(df)
    st.stop()

# =========================
# INDIVIDUAL (NÃO ALTERADO)
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
