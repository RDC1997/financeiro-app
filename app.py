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

except Exception as e:
    st.error(f"❌ Erro ao ligar ao Google Sheets: {e}")
    st.stop()

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
    df["Data"] = pd.to_datetime(
        df["Data"],
        errors="coerce"
    ).dt.date

    df["sheet_row"] = df.index + 2
    df["MesAno"] = pd.to_datetime(df["Data"]).dt.strftime("%m/%Y")

    return df


df = load_data()

# =========================
# CICLO POR SALÁRIO
# =========================
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

    if not last_salary:
        return df[df["Pessoa"] == pessoa]

    return df[
        (df["Pessoa"] == pessoa) &
        (df["Data"] >= last_salary)
    ]

# =========================
# DELETE SEGURO
# =========================
def delete_row_safe(target_row):
    fresh_raw = sheet.get_all_values()

    if len(fresh_raw) < target_row:
        return False

    try:
        sheet.delete_rows(int(target_row))
        return True
    except Exception as e:
        st.error(f"Erro ao eliminar: {e}")
        return False

# =========================
# DASHBOARD
# =========================
def mostrar_dashboard(df_pessoa, pessoa):
    st.markdown(f"## 📈 Dashboard de {pessoa}")

    receitas = df_pessoa[
        df_pessoa["Tipo"].isin(
            ["Salário", "Subsídio Alimentação"]
        )
    ]

    despesas = df_pessoa[
        df_pessoa["Tipo"] == "Despesa"
    ]

    total_receitas = receitas["Valor"].sum()
    total_despesas = despesas["Valor"].sum()
    saldo_atual = total_receitas - total_despesas

    maior_categoria = "—"

    if not despesas.empty:
        maior = (
            despesas.groupby("Categoria")["Valor"]
            .sum()
            .sort_values(ascending=False)
        )

        if not maior.empty:
            maior_categoria = maior.index[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("💰 Receitas", f"€ {total_receitas:.2f}")
    c2.metric("💸 Despesas", f"€ {total_despesas:.2f}")
    c3.metric("🏦 Saldo Atual", f"€ {saldo_atual:.2f}")
    c4.metric("🔥 Maior Gasto", maior_categoria)

    if not despesas.empty:
        st.markdown("### 📊 Despesas por Categoria")

        grafico = (
            despesas.groupby("Categoria")["Valor"]
            .sum()
            .reset_index()
        )

        st.bar_chart(
            grafico.set_index("Categoria")
        )

    st.markdown("---")

# =========================
# HISTÓRICO MENSAL
# =========================
def mostrar_historico_mensal(df, pessoa):
    st.markdown("## 📅 Histórico Mensal")

    df_pessoa = df[df["Pessoa"] == pessoa].copy()

    if df_pessoa.empty:
        st.info("Sem histórico disponível")
        return

    meses = sorted(
        df_pessoa["MesAno"].dropna().unique(),
        reverse=True
    )

    mes_escolhido = st.selectbox(
        "Seleciona o mês",
        meses
    )

    df_mes = df_pessoa[
        df_pessoa["MesAno"] == mes_escolhido
    ]

    receitas = df_mes[
        df_mes["Tipo"].isin(
            ["Salário", "Subsídio Alimentação"]
        )
    ]

    despesas = df_mes[
        df_mes["Tipo"] == "Despesa"
    ]

    total_receitas = receitas["Valor"].sum()
    total_despesas = despesas["Valor"].sum()
    saldo = total_receitas - total_despesas

    maior_categoria = "—"

    if not despesas.empty:
        top = (
            despesas.groupby("Categoria")["Valor"]
            .sum()
            .sort_values(ascending=False)
        )

        if not top.empty:
            maior_categoria = top.index[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("💰 Receitas", f"€ {total_receitas:.2f}")
    c2.metric("💸 Despesas", f"€ {total_despesas:.2f}")
    c3.metric("🏦 Saldo", f"€ {saldo:.2f}")
    c4.metric("🔥 Maior Gasto", maior_categoria)

    if not despesas.empty:
        st.markdown("### 📊 Despesas do mês")

        grafico = (
            despesas.groupby("Categoria")["Valor"]
            .sum()
            .reset_index()
        )

        st.bar_chart(
            grafico.set_index("Categoria")
        )

    st.markdown("---")

# =========================
# ICONS
# =========================
avatars = {
    "Ruben": "🤴",
    "Gabi": "👸"
}

# =========================
# MODO
# =========================
modo = st.sidebar.selectbox(
    "Modo",
    ["Casal", "Ruben", "Gabi"]
)

# =========================
# CASAL
# =========================
if modo == "Casal":

    st.subheader("📊 Visão Geral")

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars[pessoa]} {pessoa}")

        df_p = filtrar_ciclo(df, pessoa)

        mostrar_dashboard(df_p, pessoa)
        mostrar_historico_mensal(df, pessoa)

    st.stop()

# =========================
# INDIVIDUAL
# =========================
st.subheader(f"{avatars[modo]} {modo}")

pessoa = modo

df_pessoal = filtrar_ciclo(df, pessoa)

mostrar_dashboard(df_pessoal, pessoa)
mostrar_historico_mensal(df, pessoa)

# =========================
# ADICIONAR
# =========================
tipo = st.selectbox(
    "Tipo",
    ["Salário", "Subsídio Alimentação", "Despesa"]
)

categoria = ""
descricao = ""

if tipo == "Despesa":
    categoria = st.selectbox(
        "Categoria",
        [
            "Renda",
            "Vodafone",
            "Gasolina",
            "Alimentação",
            "Luz",
            "Água",
            "Outros"
        ]
    )

    if categoria == "Outros":
        descricao = st.text_input(
            "Descrição obrigatória"
        )

valor = st.number_input(
    "Valor (€)",
    min_value=0.0
)

data = st.date_input(
    "Data",
    datetime.today()
)

if data > datetime.today().date():
    st.error("Não podes escolher data futura")
    st.stop()

if st.button("Adicionar"):

    if (
        tipo == "Despesa"
        and categoria == "Outros"
        and descricao.strip() == ""
    ):
        st.error(
            "❌ Tens de preencher a descrição quando escolheste 'Outros'"
        )
        st.stop()

    sheet.append_row([
        pessoa,
        tipo,
        categoria,
        descricao,
        float(valor),
        str(data)
    ])

    st.cache_data.clear()
    st.success("Adicionado com sucesso")
    st.rerun()

# =========================
# ELIMINAR
# =========================
st.markdown("---")
st.subheader("🗑 Eliminar registos")

df_user = df[
    df["Pessoa"] == modo
].sort_values(
    "Data",
    ascending=False
)

for _, row in df_user.iterrows():

    c1, c2, c3, c4, c5 = st.columns(
        [2, 3, 2, 2, 1]
    )

    c1.write(row.get("Pessoa", ""))
    c2.write(row.get("Tipo", ""))
    c3.write(row.get("Categoria", ""))
    c4.write(f"€ {row.get('Valor', 0):.2f}")

    if c5.button(
        "❌",
        key=f"del_{row['sheet_row']}"
    ):

        deleted = delete_row_safe(
            row["sheet_row"]
        )

        if deleted:
            st.cache_data.clear()
            st.success("Registo eliminado com sucesso")
            st.rerun()
        else:
            st.error(
                "Não foi possível eliminar o registo"
            )
