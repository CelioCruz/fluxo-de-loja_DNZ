import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_venda_receita():
    st.subheader("💊 VENDA COM RECEITA")
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

    vendedor = st.selectbox("Vendedor", vendedores, index=None, placeholder="Selecione", key="vend_venda")
    cliente = st.text_input("Nome do Cliente", key="cliente_venda_input").strip().upper()

    st.markdown("### 🔘 Tipo de Registro:")
    cols = st.columns(3)
    with cols[0]:
        if st.button("✅ VENDA", use_container_width=True, type="primary"):
            st.session_state.tipo_registro = "VENDA"; st.session_state.cliente_venda = cliente; st.session_state.vendedor_venda = vendedor; st.rerun()
    with cols[1]:
        if st.button("❌ PERDA", use_container_width=True, type="secondary"):
            st.session_state.tipo_registro = "PERDA"; st.session_state.cliente_venda = cliente; st.session_state.vendedor_venda = vendedor; st.rerun()
    with cols[2]:
        if st.button("🗓️ RESERVA", use_container_width=True, type="secondary"):
            st.session_state.tipo_registro = "RESERVA"; st.session_state.cliente_venda = cliente; st.session_state.vendedor_venda = vendedor; st.rerun()

    if 'tipo_registro' in st.session_state:
        tipo = st.session_state.tipo_registro
        cli = st.session_state.cliente_venda
        vend = st.session_state.vendedor_venda
        st.markdown("---")
        st.success(f"✅ **PRONTO**: {cli} | **Tipo:** {tipo}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("↩️ VOLTAR", use_container_width=True):
                del st.session_state.tipo_registro; st.session_state.etapa = 'atendimento'; st.rerun()
        with col2:
            if st.button("✅ CONFIRMAR", type="primary", use_container_width=True):
                if not vend or not cli: st.error("⚠️ Preencha Vendedor e Cliente!")
                else:
                    dados = {
                        'loja': st.session_state.loja, 'vendedor': vend, 'cliente': cli,
                        'atendimento': '1', 'receita': '1',
                        'venda': '1' if tipo == "VENDA" else '',
                        'perda': '1' if tipo == "PERDA" else '',
                        'reserva': '1' if tipo == "RESERVA" else '',
                        'pesquisa': '', 'consulta': ''
                    }
                    if gsheets.registrar_atendimento(dados):
                        st.balloons(); st.success("✅ Registro salvo!")
                        del st.session_state.tipo_registro; st.session_state.etapa = 'loja'; st.rerun()
                    else: st.error("❌ Erro ao salvar.")

