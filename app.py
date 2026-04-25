# =========================
# CASAL
# =========================
if modo == "Casal 👨‍❤️‍👩":

    st.subheader("👨‍❤️‍👩 Casal - PRO 2.1 Inteligente")

    def get_last_salary(df, pessoa):
        df_p = df[(df["Pessoa"] == pessoa) & (df["Tipo"] == "Salário")]
        if df_p.empty:
            return None
        return df_p.sort_values("Data", ascending=False).iloc[0]["Data"]

    def filtrar_ciclo(df, pessoa):
        last_salary = get_last_salary(df, pessoa)

        if last_salary:
            return df[(df["Pessoa"] == pessoa) & (df["Data"] >= last_salary)]
        else:
            return df[df["Pessoa"] == pessoa]

    for pessoa in ["Ruben", "Gabi"]:

        st.markdown(f"## {avatars.get(pessoa, '👤')} {pessoa}")

        df_p = filtrar_ciclo(df, pessoa)

        receitas = df_p[df_p["Tipo"].isin(["Salário", "Subsídio Alimentação"])]
        despesas = df_p[df_p["Tipo"] == "Despesa"]

        total_receitas = receitas["Valor"].sum()
        total_despesas = despesas["Valor"].sum()
        saldo = total_receitas - total_despesas

        taxa_poupanca = (saldo / total_receitas * 100) if total_receitas > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Receitas", f"{total_receitas:.2f} €")
        c2.metric("💸 Despesas", f"{total_despesas:.2f} €")
        c3.metric("📊 Saldo", f"{saldo:.2f} €")

        # =========================
        # GRÁFICO (seguro mesmo se vazio)
        # =========================
        if not despesas.empty:
            chart_df = despesas.groupby("Categoria", as_index=False)["Valor"].sum()
            st.bar_chart(chart_df.set_index("Categoria"))

        st.markdown("### 💰 Receitas")

        if not receitas.empty:
            st.dataframe(receitas, use_container_width=True)
        else:
            st.info("Sem receitas neste ciclo")

        st.markdown("### 💸 Despesas")

        if not despesas.empty:
            st.dataframe(despesas, use_container_width=True)
        else:
            st.info("Sem despesas neste ciclo")

        # =========================
        # 🧠 INSIGHTS
        # =========================
        st.markdown("### 🧠 Análise rápida")

        if total_receitas == 0 and total_despesas == 0:
            st.info("Ainda não há dados suficientes neste ciclo.")
        else:
            if saldo < 0:
                st.error("⚠️ Estás em saldo negativo neste ciclo.")
            elif taxa_poupanca < 10:
                st.warning("⚠️ Pouca margem de poupança.")
            elif taxa_poupanca > 25:
                st.success("🟢 Excelente controlo financeiro.")
            else:
                st.info("📊 Estás equilibrado neste ciclo.")

        st.markdown("---")

        # =========================
        # 🗑 ELIMINAR REGISTOS (seguro)
        # =========================
        st.markdown("#### 🗑 Eliminar registos")

        if df_p.empty:
            st.info("Sem registos para eliminar.")
        else:
            for _, row in df_p.iterrows():

                c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])

                c1.write(row.get("Pessoa", ""))
                c2.write(row.get("Tipo", ""))
                c3.write(row.get("Categoria", ""))
                c4.write(f"{row.get('Valor', 0):.2f} €")

                if c5.button("❌", key=str(row.get("ID", ""))):
                    try:
                        data = sheet.get_all_values()
                        headers = data[0]
                        id_index = headers.index("ID")

                        for i, r in enumerate(data[1:], start=2):
                            if r[id_index] == row["ID"]:
                                sheet.delete_rows(i)
                                break

                        refresh()

                    except Exception as e:
                        st.error(f"Erro ao eliminar: {e}")

    st.stop()
