import streamlit as st

def tela_selecao_loja():
    st.title("🏪 SELECIONE A LOJA")
    lojas = [f"LOJA {str(i).zfill(2)}" for i in range(1, 8)]
    loja = st.selectbox("Selecione sua loja:", lojas, index=0, key="loja_select")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ CONFIRMAR", use_container_width=True, key="btn_confirmar_loja"):
            st.session_state.loja = loja
            st.session_state.etapa = 'atendimento'
            st.rerun()
    with col2:
        if st.button("↩️ VOLTAR", use_container_width=True, key="btn_voltar_loja"):
            st.session_state.etapa = 'loguin'
            st.rerun()