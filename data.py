import streamlit as st
import pandas as pd

SHEET_ID = "LOCAL_MODE"

# =========================
# BASE LOCAL
# =========================

if "finance_data" not in st.session_state:
    st.session_state.finance_data = pd.DataFrame(columns=[
        "ID",
        "Pessoa",
        "Tipo",
        "Categoria",
        "Descrição",
        "Valor",
        "Data"
    ])

if "categories" not in st.session_state:
    st.session_state.categories = [
        "Casa",
        "Comida",
        "Transporte",
        "Lazer",
        "Saúde"
    ]

if "goals" not in st.session_state:
    st.session_state.goals = pd.DataFrame(columns=[
        "Meta",
        "Objetivo",
        "Atual"
    ])

# =========================
# LOAD DATA
# =========================

@st.cache_data(ttl=60)
def load_data():
    return st.session_state.finance_data.copy()

# =========================
# CATEGORIAS
# =========================

def add_category(cat):
    if cat not in st.session_state.categories:
        st.session_state.categories.append(cat)

def delete_category(cat):
    if cat in st.session_state.categories:
        st.session_state.categories.remove(cat)

# =========================
# FILTROS
# =========================

def aplicar_filtros(df, ano, mes, pesquisa, meses):

    df_filtrado = df.copy()

    if ano != "Todos" and not df_filtrado.empty:
        df_filtrado = df_filtrado[
            pd.to_datetime(df_filtrado["Data"]).dt.year == int(ano)
        ]

    if mes != "Todos" and not df_filtrado.empty:
        mes_num = meses.index(mes)

        df_filtrado = df_filtrado[
            pd.to_datetime(df_filtrado["Data"]).dt.month == mes_num
        ]

    if pesquisa.strip() and not df_filtrado.empty:

        pesquisa = pesquisa.lower()

        df_filtrado = df_filtrado[
            df_filtrado.astype(str)
            .apply(lambda x: x.str.lower())
            .apply(lambda x: x.str.contains(pesquisa))
            .any(axis=1)
        ]

    return df_filtrado

# =========================
# METAS
# =========================

def load_goals():
    return st.session_state.goals.copy()

def add_goal(nome, objetivo):

    nova = pd.DataFrame([{
        "Meta": nome,
        "Objetivo": objetivo,
        "Atual": 0
    }])

    st.session_state.goals = pd.concat(
        [st.session_state.goals, nova],
        ignore_index=True
    )

def update_goal(nome, valor):

    idx = st.session_state.goals[
        st.session_state.goals["Meta"] == nome
    ].index

    if len(idx):
        st.session_state.goals.loc[idx, "Atual"] += valor

def delete_goal(nome):

    st.session_state.goals = st.session_state.goals[
        st.session_state.goals["Meta"] != nome
    ]

# =========================
# SHEET FAKE
# =========================

class FakeSheet:

    def append_row(self, row):

        nova = pd.DataFrame([{
            "ID": row[0],
            "Pessoa": row[1],
            "Tipo": row[2],
            "Categoria": row[3],
            "Descrição": row[4],
            "Valor": row[5],
            "Data": row[6]
        }])

        st.session_state.finance_data = pd.concat(
            [st.session_state.finance_data, nova],
            ignore_index=True
        )

    def get_all_values(self):

        headers = [
            "ID",
            "Pessoa",
            "Tipo",
            "Categoria",
            "Descrição",
            "Valor",
            "Data"
        ]

        rows = st.session_state.finance_data.fillna("").values.tolist()

        return [headers] + rows

    def delete_rows(self, row_number):

        idx = row_number - 2

        if idx >= 0 and idx < len(st.session_state.finance_data):

            st.session_state.finance_data = (
                st.session_state.finance_data
                .drop(st.session_state.finance_data.index[idx])
                .reset_index(drop=True)
            )

sheet = FakeSheet()
