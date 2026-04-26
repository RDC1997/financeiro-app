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
st.set_page_config(page_title="Rubi&Gabi Finance PRO 2.1", layout="wide")
st.title("💰 Controlo Financeiro PRO 2.1")

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
# CATEGORIAS
# =========================
@st.cache_data(ttl=30)
def load_categories():
    data = cat_sheet.get_all_values()
    return [row[0] for row in data[1:] if row[0].strip() != ""]

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
# DATA
# =========================
@st.cache_data(ttl=30)
def load_data():
    raw = sheet.get_all_values()
    cols = ["ID", "Pessoa", "Tipo", "Categoria", "Descrição", "Valor", "Data"]

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
    ["Casal 👨‍❤️‍👩", "Ruben 🤴", "Gabi 👸", "Metas 🎯"]
)

avatars = {
    "Ruben": "🤴",
    "Gabi": "👸"
}

# =========================
# CATEGORIAS UI
# =========================
st.sidebar.markdown("## ⚙️ Categorias")

with st.sidebar.expander("➕ Adicionar categoria"):
    new_cat = st.text_input("Nova categoria")

    if st.button("Adicionar categoria"):
        if new_cat.strip():
            add_category(new_cat.strip())
            refresh()

with st.sidebar.expander("❌ Remover categoria"):
    if categories:
        cat_del = st.selectbox("Escolher", categories)

        if st.button("Remover categoria"):
            delete_category(cat_del)
            refresh()

with st.sidebar.expander("📋 Ver categorias"):
    st.write(categories)

# =========================
# CASAL + ALERTAS PRO
# =========================
if modo == "Casal 👨‍❤️‍👩":

    st.subheader("👨‍❤️‍👩 Casal - PRO 2 Inteligente")

    def get_last_salary(df, pessoa):
        df_p = df[
            (df["Pessoa"] == pessoa) &
            (df["Tipo"] == "Salário")
        ]

        if df_p.empty:
            return None

        return df_p.sort_values(
            "Data",
            ascending=False
        ).iloc[0]["Data"]

    def filtrar_ciclo(df, pessoa):
        last_salary = get_last_salary(df, pessoa)

        if last_salary:
            return df[
                (df["Pessoa"] == pessoa) &
                (df["Data"] >= last_salary)
            ]

        return df[df["Pessoa"] == pessoa]

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = filtrar_ciclo(df, pessoa)

        receitas = df_p[
            df_p["Tipo"].isin([
                "Salário",
                "Subsídio Alimentação"
            ])
        ]

        despesas = df_p[
            df_p["Tipo"] == "Despesa"
        ]

        total_receitas = receitas["Valor"].sum()
        total_despesas = despesas["Valor"].sum()
        saldo = total_receitas - total_despesas

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "💰 Receitas",
            f"{total_receitas:.2f} €"
        )

        c2.metric(
            "💸 Despesas",
            f"{total_despesas:.2f} €"
        )

        c3.metric(
            "📊 Saldo",
            f"{saldo:.2f} €"
        )

        st.markdown("### 💰 Receitas")
        st.dataframe(receitas, use_container_width=True)

        st.markdown("### 💸 Despesas")
        st.dataframe(despesas, use_container_width=True)

        # =========================
        # 🧠 ANÁLISE BASE
        # =========================
        st.markdown("### 🧠 Análise do ciclo")

        if total_receitas == 0 and total_despesas == 0:
            st.info("Sem dados suficientes para análise neste ciclo.")
        else:
            taxa = (
                saldo / total_receitas * 100
                if total_receitas > 0 else 0
            )

            if saldo < 0:
                st.error("⚠️ Estás em défice neste ciclo.")
            elif taxa < 10:
                st.warning("⚠️ Poupança baixa neste ciclo.")
            elif taxa < 25:
                st.info("📊 Estás equilibrado.")
            else:
                st.success("🟢 Excelente controlo financeiro!")

        # =========================
        # 🚨 ALERTAS INTELIGENTES PRO
        # =========================
        st.markdown("### 🚨 Alertas Inteligentes PRO")

        if total_despesas > total_receitas:
            st.error("🚨 Estás a gastar mais do que ganhas!")

        elif total_despesas > 0.8 * total_receitas:
            st.warning("⚠️ Estás perto do limite do teu rendimento")

        if not despesas.empty:
            cat_sum = despesas.groupby("Categoria")["Valor"].sum()

            if not cat_sum.empty:
                if (cat_sum.max() / total_despesas) > 0.4:
                    st.warning("⚠️ Uma categoria está a dominar os gastos")

        if (
            total_receitas > 0 and
            saldo > 0 and
            (saldo / total_receitas) > 0.25
        ):
            st.success("🟢 Excelente controlo financeiro!")

        st.markdown("#### 🗑 Eliminar registos")

        for _, row in df_p.iterrows():

            c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])

            c1.write(row["Pessoa"])
            c2.write(row["Tipo"])
            c3.write(row["Categoria"])
            c4.write(row["Valor"])

            if c5.button("❌", key=row["ID"]):
                data = sheet.get_all_values()
                headers = data[0]
                id_index = headers.index("ID")

                for i, r in enumerate(data[1:], start=2):
                    if r[id_index] == row["ID"]:
                        sheet.delete_rows(i)
                        break

                refresh()

    st.stop()

# =========================
# METAS (SEM EMPTY TABLE)
# =========================
if modo == "Metas 🎯":

    st.subheader("🎯 Metas")

    def load_goals():
        raw = goal_sheet.get_all_values()

        if len(raw) > 1:
            return pd.DataFrame(raw[1:], columns=raw[0])

        return pd.DataFrame()

    goals = load_goals()

    with st.expander("➕ Criar meta"):
        nome = st.text_input("Nome")
        obj = st.number_input(
            "Objetivo (€)",
            min_value=0.0
        )

        if st.button("Criar meta"):
            if nome.strip():
                goal_sheet.append_row([nome, obj, 0])
                refresh()

    st.markdown("### 📊 Metas atuais")

    if goals.empty:
        st.info("Ainda não existem metas criadas.")
    else:
        st.dataframe(goals, use_container_width=True)

    st.stop()

# =========================
# INDIVIDUAL
# =========================
pessoa = modo.split()[0]

st.subheader(f"{avatars.get(pessoa, '👤')} {pessoa}")

tipo = st.selectbox(
    "Tipo",
    ["Salário", "Subsídio Alimentação", "Despesa"]
)

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox(
        "Categoria",
        categories if categories else ["Outros"]
    )

    # Só mostra descrição se for "Outros"
    if categoria == "Outros":
        descricao = st.text_input("Descrição obrigatória")

valor = st.number_input(
    "Valor (€)",
    min_value=0.0
)

data = st.date_input(
    "Data",
    datetime.today()
)

if st.button("Adicionar"):

    # validação obrigatória para Outros
    if (
        tipo == "Despesa" and
        categoria == "Outros" and
        descricao.strip() == ""
    ):
        st.error("❌ Tens de preencher a descrição quando escolhes 'Outros'")
        st.stop()

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
