import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_consulta():
    st.subheader("📅 CONFIRMAR")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    if 'gsheets' not in st.session_state:
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    # Carrega vendedores
    vendedores_data = gsheets.get_vendedores_por_loja()
    vendedores = [v['VENDEDOR'] for v in vendedores_data] if vendedores_data else []

    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
        return

    # Campos do formulário
    cliente = st.text_input("Nome do Paciente", key="cliente_consulta_input").upper()
    vendedor = st.selectbox("Vendedor", vendedores, index=None, placeholder="Selecione", key="vend_consulta")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ CONFIRMAR", type="primary", key="btn_registrar_consulta"):
            if not cliente.strip() or not vendedor:
                st.error("⚠️ Preencha todos os campos!")
            else:
                # Salva dados da consulta
                dados = {
                    'loja': st.session_state.loja,
                    'atendente': st.session_state.nome_atendente,
                    'cliente': cliente,
                    'data': datetime.now().strftime("%d/%m/%Y"),
                    'atendimento': '1',
                    'receita': '', 'venda': '', 'perda': '', 'reserva': '',
                    'pesquisa': '',  'consulta': '1',
                    'hora': datetime.now().strftime("%H:%M")
                }

                if gsheets.registrar_sem_vendedor(dados):
                    st.balloons()
                    st.success("✅ Consulta registrada!")

                    # ✅ Passa os dados para a tela de encaminhamento
                    st.session_state.enc_cliente = cliente
                    st.session_state.enc_vendedor = vendedor 

                    # Vai para tela_encaminhamento
                    st.session_state.etapa = 'subtela'
                    st.session_state.subtela = 'encaminhamento' 
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar no Google Sheets.")

    with col2:
        if st.button("↩️ Voltar", key="btn_voltar_consulta"):
            st.session_state.etapa = 'atendimento'
            st.rerun()