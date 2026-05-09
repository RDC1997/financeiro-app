import streamlit as st
import pandas as pd
from io import BytesIO
import uuid

def export_to_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')

    return output.getvalue()

def refresh():
    st.rerun()

def validate_value(valor):
    if valor <= 0:
        return "O valor deve ser maior que 0"
    return None

def validate_category(tipo, categoria, descricao):
    if tipo == "Despesa":
        if not categoria:
            return "Selecione uma categoria"

        if categoria == "Outros" and not descricao.strip():
            return "Adicione uma descrição"

    return None

def generate_id():
    return str(uuid.uuid4())[:8]
