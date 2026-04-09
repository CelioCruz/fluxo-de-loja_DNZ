import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_google_registro():
    st.subheader("🌐 REGISTRO DE CONSULTA GOOGLE")
    st.info(f"**Loja:** {st.session_state.loja} | **Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    if 'gsheets' not in st.session_state:
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    # Carregar vendedores
    vendedores_data = gsheets.get_vendedores_por_loja()
    vendedores = [v['VENDEDOR'] for v in vendedores_data]
    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
        if st.button("↩️ Voltar"): st.session_state.etapa = 'atendimento'; st.rerun()
        return

    # Formulário
    vendedor = st.selectbox("Selecione o Vendedor", vendedores, index=None, placeholder="Escolha o vendedor...", key="vend_google")
    cliente = st.text_input("Nome do Cliente", key="cliente_google_input").strip().upper()

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ CONFIRMAR", type="primary", use_container_width=True):
            if not vendedor or not cliente:
                st.error("⚠️ Preencha Vendedor e Cliente!")
            else:
                # Prepara os dados para salvar na planilha
                dados = {
                    'loja': st.session_state.loja,
                    'vendedor': vendedor,
                    'cliente': cliente,
                    'atendimento': '1',
                    'google': '1', # Grava o valor 1 na coluna M
                    'receita': '', 'venda': '', 'perda': '', 'reserva': '', 'pesquisa': '', 'consulta': ''
                }
                
                if gsheets.registrar_atendimento(dados):
                    st.balloons()
                    st.success(f"✅ Registro do Google para {cliente} salvo com sucesso!")
                    # Pequeno delay antes de voltar
                    st.session_state.etapa = 'loja'
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar no Google Sheets.")

    with col2:
        if st.button("↩️ CANCELAR", use_container_width=True):
            st.session_state.etapa = 'atendimento'
            st.rerun()

