# (continuação do teu código base — só alterações relevantes adicionadas)

# =========================
# CATEGORIAS (FIXAS + SHEET + GESTÃO)
# =========================
@st.cache_data(ttl=30)
def load_categories():
    try:
        data = cat_sheet.get_all_values()
        sheet_cats = [r[0] for r in data[1:] if r[0].strip()]
    except:
        sheet_cats = []

    fixed = ["Renda","Vodafone","Gasolina","Alimentação","Luz","Água","Outros"]

    return list(dict.fromkeys(fixed + sheet_cats))

def add_category(cat):
    cat_sheet.append_row([cat])

def delete_category(cat):
    data = cat_sheet.get_all_values()

    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == cat:
            cat_sheet.delete_rows(i + 1)
            break

categories = load_categories()

# =========================
# SIDEBAR - GESTÃO DE CATEGORIAS (NOVO CORRIGIDO)
# =========================
st.sidebar.markdown("## ⚙️ Categorias")

with st.sidebar.expander("➕ Adicionar categoria"):
    new_cat = st.text_input("Nova categoria")

    if st.button("Adicionar categoria"):
        if new_cat.strip():
            add_category(new_cat.strip())
            st.cache_data.clear()
            st.success("Categoria adicionada")
            st.rerun()

with st.sidebar.expander("❌ Remover categoria"):
    if categories:
        cat_to_remove = st.selectbox("Escolhe categoria", categories)

        if st.button("Remover categoria"):
            delete_category(cat_to_remove)
            st.cache_data.clear()
            st.success("Categoria removida")
            st.rerun()
    else:
        st.info("Sem categorias disponíveis")
