# Roadmap de melhorias para a app Rubi&Gabi
# Implementar por esta ordem (recomendado)

# PRIORIDADE 1 — FUNDAMENTAL
# 1. Separar Receitas vs Despesas + Saldo Real
# 2. Filtro por Mês e Ano
# 3. Proteção contra erros
# 4. Dashboard por Categoria

# PRIORIDADE 2 — MELHORIA FORTE
# 5. Edição de Registos
# 6. Alertas Inteligentes
# 7. Metas Financeiras

# PRIORIDADE 3 — PREMIUM
# 8. Design mais premium
# 9. Backup Automático


# LÓGICA RECOMENDADA

# ---------------------------------
# RECEITAS / DESPESAS / SALDO
# ---------------------------------

# receitas = df[df['Tipo'].isin(['Salário', 'Subsídio Alimentação'])]['Valor'].sum()
# despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
# saldo = receitas - despesas

# Mostrar:
# st.metric('Receitas', f'€ {receitas:.2f}')
# st.metric('Despesas', f'€ {despesas:.2f}')
# st.metric('Saldo', f'€ {saldo:.2f}')


# ---------------------------------
# FILTRO POR MÊS E ANO
# ---------------------------------

# meses = sorted(df['Mês'].unique())
# anos = sorted(df['Ano'].unique())

# mes_filtro = st.selectbox('Mês', meses)
# ano_filtro = st.selectbox('Ano', anos)

# df = df[
#     (df['Mês'] == mes_filtro) &
#     (df['Ano'] == ano_filtro)
# ]


# ---------------------------------
# PROTEÇÃO CONTRA ERROS
# ---------------------------------

# if valor <= 0:
#     st.error('O valor precisa ser maior que zero.')
#     st.stop()

# if tipo == 'Despesa' and categoria == '':
#     st.error('Seleciona uma categoria.')
#     st.stop()

# if categoria == 'Outros' and descricao.strip() == '':
#     st.error('Preenche a descrição.')
#     st.stop()


# ---------------------------------
# DASHBOARD POR CATEGORIA
# ---------------------------------

# despesas_df = df[df['Tipo'] == 'Despesa']

# categoria_total = despesas_df.groupby('Categoria')['Valor']\
#     .sum()\
#     .reset_index()

# fig = px.pie(
#     categoria_total,
#     names='Categoria',
#     values='Valor',
#     title='Despesas por Categoria'
# )

# st.plotly_chart(fig, use_container_width=True)


# ---------------------------------
# ALERTAS INTELIGENTES
# ---------------------------------

# if despesas > receitas:
#     st.warning('⚠️ As despesas ultrapassaram as receitas este mês.')

# if not categoria_total.empty:
#     top = categoria_total.sort_values('Valor', ascending=False).iloc[0]
#     st.info(
#         f"Maior gasto: {top['Categoria']} → € {top['Valor']:.2f}"
#     )


# ---------------------------------
# META FINANCEIRA
# ---------------------------------

# meta = 10000
# progresso = max(0, min(saldo / meta, 1.0))

# st.subheader('🎯 Meta Financeira')
# st.progress(progresso)
# st.write(f'Objetivo: € {meta:.2f}')
# st.write(f'Atual: € {saldo:.2f}')


# ---------------------------------
# BACKUP CSV
# ---------------------------------

# csv = df.to_csv(index=False).encode('utf-8')

# st.download_button(
#     label='⬇️ Exportar CSV',
#     data=csv,
#     file_name='backup_financas.csv',
#     mime='text/csv'
# )


# ---------------------------------
# EDIÇÃO DE REGISTOS
# ---------------------------------

# Esta parte exige mais cuidado porque editar no Google Sheets
# precisa identificar corretamente a linha real.
# Recomendo implementar depois de tudo acima estar estável.


# NOTA IMPORTANTE
# Não tentes fazer tudo no mesmo dia.
# Faz por blocos:
# primeiro saldo + filtro,
# depois categoria + alertas,
# depois edição.
# Isso evita bugs e confusão.
