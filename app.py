
 import streamlit as st
 import pandas as pd
 from datetime import datetime, timedelta
 import uuid
 import time
 import plotly.express as px
 import plotly.graph_objects as go
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
 st.title("Gestão Financeira")
 
 # =========================
 # SESSION STATE
 # =========================
 if 'inputs' not in st.session_state:
     st.session_state.inputs = {
         'valor': 0.0,
         'descricao': '',
         'categoria': ''
     }
 
 if 'confirm_delete' not in st.session_state:
     st.session_state.confirm_delete = None
 
 if 'filtros' not in st.session_state:
     st.session_state.filtros = {
         'mes': None,
         'ano': None,
         'pesquisa': ''
     }
 
 # =========================
 # HELPERS
 # =========================
 def refresh():
     st.cache_data.clear()
     # Limpar cache específico
     load_data.clear()
     load_categories.clear()
     try:
         load_goals.clear()
     except:
         pass
     st.rerun()
 
 def generate_id():
     return str(uuid.uuid4())
 
 def reset_inputs():
     st.session_state.inputs = {
         'valor': 0.0,
         'descricao': '',
         'categoria': ''
     }
 
 def export_to_excel(df):
     try:
         output = BytesIO()
         with pd.ExcelWriter(output, engine='openpyxl') as writer:
             df.to_excel(writer, index=False, sheet_name='Dados')
         return output.getvalue()
     except Exception as e:
         # Fallback: retornar CSV se Excel falhar
         return df.to_csv(index=False).encode('utf-8')
 
 # Contador de chamadas API (para debug)
 if 'api_calls' not in st.session_state:
     st.session_state.api_calls = 0
 
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
 # CATEGORIAS
 # =========================
 @st.cache_data(ttl=300)  # Cache por 5 minutos
 def load_categories():
     data = cat_sheet.get_all_values()
     return [row[0] for row in data[1:] if row[0].strip() != ""]
 
 def add_category(cat):
     cat_sheet.append_row([cat])
     # Limpar cache após adicionar
     load_categories.clear()
 
 def delete_category(cat):
     data = cat_sheet.get_all_values()
     for i, row in enumerate(data):
         if i == 0:
             continue
         if row[0] == cat:
             cat_sheet.delete_rows(i + 1)
             break
     # Limpar cache após eliminar
     load_categories.clear()
 
 categories = load_categories()
 
 # =========================
 # DATA
 # =========================
 @st.cache_data(ttl=300)  # Cache por 5 minutos
 def load_data():
     raw = sheet.get_all_values()
     cols = ["ID","Pessoa","Tipo","Categoria","Descrição","Valor","Data"]
 
     if len(raw) < 2:
         return pd.DataFrame(columns=cols)
 
     df = pd.DataFrame(raw[1:], columns=raw[0])
 
     df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
     # Converter Data e manter apenas a parte da data (sem hora)
     df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date
 
     return df
 
 df = load_data()
 
 # =========================
 # MENU
 # =========================
 modo = st.sidebar.selectbox(
     "Modo",
     ["Casal 👨‍❤️‍👩","Ruben 🤴","Gabi 👸","Metas 🎯","Análises 📊"]
 )
 
 avatars = {"Ruben":"🤴","Gabi":"👸"}
 
 # =========================
 # CATEGORIAS UI
 # =========================
 st.sidebar.markdown("## ⚙️ Categorias")
 
 with st.sidebar.expander("➕ Adicionar categoria"):
     new_cat = st.text_input("Nova categoria", key="new_cat_input")
 
     if st.button("Adicionar categoria", key="add_cat"):
         if new_cat.strip():
             add_category(new_cat.strip())
             refresh()
 
 with st.sidebar.expander("❌ Remover categoria"):
     if categories:
         cat_del = st.selectbox("Escolher", categories, key="cat_del_select")
 
         if st.button("Remover categoria", key="del_cat"):
             delete_category(cat_del)
             refresh()
 
 with st.sidebar.expander("📋 Ver categorias"):
     if categories:
         # Contagem de registos por categoria
         contagem = df[df["Tipo"] == "Despesa"].groupby('Categoria').size()
         for cat in categories:
             qtd = contagem.get(cat, 0)
             st.write(f"• {cat}: {qtd} registos")
     else:
         st.write("Sem categorias")
 
 # =========================
 # FILTROS
 # =========================
 st.sidebar.markdown("---")
 st.sidebar.markdown("## 🔍 Filtros")
 
 # Verificar se há dados válidos
 try:
     anos_disponiveis = sorted(df["Data"].dt.year.unique().tolist(), reverse=True) if not df.empty and "Data" in df.columns else [datetime.now().year]
 except:
     anos_disponiveis = [datetime.now().year]
 
 meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
 
 filtro_ano = st.sidebar.selectbox("Ano", ["Todos"] + anos_disponiveis, key="filtro_ano")
 filtro_mes = st.sidebar.selectbox("Mês", meses, key="filtro_mes")
 pesquisa = st.sidebar.text_input("🔎 Pesquisar", key="pesquisa")
 
 def aplicar_filtros(df, ano, mes, pesquisa):
     df_f = df.copy()
     
     if ano != "Todos":
         df_f = df_f[df_f["Data"].dt.year == int(ano)]
     
     if mes != "Todos":
         mes_idx = meses.index(mes)
         df_f = df_f[df_f["Data"].dt.month == mes_idx]
     
     if pesquisa:
         df_f = df_f[df_f["Descrição"].str.contains(pesquisa, case=False, na=False)]
     
     return df_f
 
 df_filtrado = aplicar_filtros(df, filtro_ano, filtro_mes, pesquisa)
 
 # =========================
 # CASAL
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
             return df[(df["Pessoa"] == pessoa) & (df["Data"] >= last_salary)]
         return df[df["Pessoa"] == pessoa]
 
     # Totais do casal
     df_casal = df_filtrado.copy()
     receitas_casal = df_casal[df_casal["Tipo"].isin(["Salário","Subsídio Alimentação"])]
     despesas_casal = df_casal[df_casal["Tipo"] == "Despesa"]
     
     total_receitas_casal = receitas_casal["Valor"].sum()
     total_despesas_casal = despesas_casal["Valor"].sum()
     saldo_casal = total_receitas_casal - total_despesas_casal
     
     st.markdown("### 💑 Totais do Casal")
     c1, c2, c3 = st.columns(3)
     c1.metric("💰 Receitas", f"{total_receitas_casal:.2f} €")
     c2.metric("💸 Despesas", f"{total_despesas_casal:.2f} €")
     c3.metric("📊 Saldo", f"{saldo_casal:.2f} €", delta_color="normal")
 
     st.markdown("---")
 
     for pessoa in ["Ruben", "Gabi"]:
 
         st.markdown(f"### {avatars[pessoa]} {pessoa}")
 
         df_p = filtrar_ciclo(df_filtrado, pessoa)
 
         receitas = df_p[df_p["Tipo"].isin(["Salário",…
