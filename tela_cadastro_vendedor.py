import streamlit as st
from google_planilha import GooglePlanilha

def mostrar():
    st.title("👨‍💼 GERENCIAMENTO DE VENDEDORES")
    
    if 'gsheets' not in st.session_state:
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    # Seção para cadastrar novo vendedor
    st.subheader("➕ Cadastrar Novo Vendedor")
    novo_nome = st.text_input("Nome do Vendedor").upper().strip()
    
    if st.button("💾 SALVAR VENDEDOR", use_container_width=True):
        if not novo_nome:
            st.warning("⚠️ Digite o nome do vendedor!")
        else:
            todos = gsheets.get_todos_vendedores()
            if any(v['VENDEDOR'] == novo_nome for v in todos):
                st.error("❌ Vendedor já cadastrado!")
            else:
                if gsheets.adicionar_vendedor(novo_nome):
                    st.success(f"✅ Vendedor {novo_nome} cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar no Google Sheets.")

    st.divider()

    # Seção para listar vendedores cadastrados
    st.subheader("📋 Vendedores Cadastrados")
    vendedores = gsheets.get_todos_vendedores()
    
    if not vendedores:
        st.info("Nenhum vendedor cadastrado.")
    else:
        # Cabeçalho da tabela
        col1, col2, col3 = st.columns([3, 2, 2])
        col1.markdown("**Nome**")
        col2.markdown("**Status**")
        col3.markdown("**Ação**")
        
        for v in vendedores:
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.text(v['VENDEDOR'])
            
            status_cor = "green" if v['STATUS'] == "ATIVO" else "red"
            c2.markdown(f"<span style='color:{status_cor}'>**{v['STATUS']}**</span>", unsafe_allow_html=True)
            
            novo_status = "INATIVO" if v['STATUS'] == "ATIVO" else "ATIVO"
            btn_label = "🔴 DESATIVAR" if v['STATUS'] == "ATIVO" else "🟢 ATIVAR"
            
            if c3.button(btn_label, key=f"btn_status_{v['row']}", use_container_width=True):
                if gsheets.atualizar_status_vendedor(v['row'], novo_status):
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar status.")

    if st.button("↩️ VOLTAR", use_container_width=True):
        st.session_state.etapa = 'atendimento'
        st.rerun()
