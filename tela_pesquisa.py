import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_pesquisa():
    st.subheader("🔍 PESQUISA SEM RECEITA")
    st.info(f"**Loja:** {st.session_state.loja} | **Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    if 'gsheets' not in st.session_state: st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    vendedores_data = gsheets.get_vendedores_por_loja()
    vendedores = [v['VENDEDOR'] for v in vendedores_data]
    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
        if st.button("↩️ Voltar"): st.session_state.etapa = 'atendimento'; st.rerun()
        return

    vendedor = st.selectbox("Vendedor", vendedores, index=None, placeholder="Selecione", key="vend_pesquisa")
    cliente = st.text_input("Nome do Cliente", key="cliente_pesquisa_input").strip().upper()

    st.markdown("---")

    if st.button("✅ CONFIRMAR", type="primary", key="btn_registrar_pesquisa", use_container_width=True):
        if not vendedor or not cliente: st.error("⚠️ Preencha Vendedor e Cliente!")
        else:
            st.session_state.tipo_registro = "PESQUISA"
            st.session_state.cliente_pesquisa = cliente
            st.session_state.vendedor_pesquisa = vendedor
            st.rerun()

    if 'tipo_registro' in st.session_state:
        st.success(f"✅ **PRONTO**: {st.session_state.cliente_pesquisa}")
        if st.button("💾 SALVAR ATENDIMENTO", type="primary", use_container_width=True):
            dados = {
                'loja': st.session_state.loja, 'vendedor': st.session_state.vendedor_pesquisa,
                'cliente': st.session_state.cliente_pesquisa, 'atendimento': '1', 'pesquisa': '1',
                'receita': '', 'venda': '', 'perda': '', 'reserva': '', 'consulta': ''
            }
            if gsheets.registrar_atendimento(dados):
                st.balloons(); st.success("✅ Registro salvo!")
                del st.session_state.tipo_registro
                st.session_state.etapa = 'loja'
                st.rerun()
            else: st.error("❌ Erro ao salvar.")

    if st.button("↩️ VOLTAR", use_container_width=True):
        if 'tipo_registro' in st.session_state: del st.session_state.tipo_registro
        st.session_state.etapa = 'atendimento'; st.rerun()
