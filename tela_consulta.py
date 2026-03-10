import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_consulta():
    st.subheader("📅 CONFIRMAR EXAME")
    st.info(f"**Loja:** {st.session_state.loja} | **Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    if 'gsheets' not in st.session_state: st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    vendedores_data = gsheets.get_vendedores_por_loja()
    vendedores = [v['VENDEDOR'] for v in vendedores_data] if vendedores_data else []

    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
        if st.button("↩️ Voltar"): st.session_state.etapa = 'atendimento'; st.rerun()
        return

    cliente = st.text_input("Nome do Paciente", key="cliente_consulta_input").upper()
    vendedor = st.selectbox("Vendedor", vendedores, index=None, placeholder="Selecione", key="vend_consulta")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ CONFIRMAR", type="primary", use_container_width=True):
            if not cliente.strip() or not vendedor: st.error("⚠️ Preencha todos os campos!")
            else:
                dados = {
                    'loja': st.session_state.loja, 'vendedor': vendedor, 'cliente': cliente,
                    'atendimento': '1', 'receita': '', 'venda': '', 'perda': '', 'reserva': '', 'pesquisa': '',
                    'consulta': '1'
                }
                if gsheets.registrar_atendimento(dados):
                    st.balloons(); st.success("✅ Consulta registrada!")
                    st.session_state.enc_cliente = cliente; st.session_state.enc_vendedor = vendedor
                    st.session_state.subtela = 'exame_vista'; st.session_state.etapa = 'subtela'; st.rerun()
                else: st.error("❌ Erro ao salvar.")

    with col2:
        if st.button("↩️ Voltar", use_container_width=True): st.session_state.etapa = 'atendimento'; st.rerun()

