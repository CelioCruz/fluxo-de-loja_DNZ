import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_venda_receita():
    st.subheader("💊 VENDA COM RECEITA")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    if 'gsheets' not in st.session_state:
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    # Carrega vendedores
    vendedores_data = gsheets.get_vendedores_por_loja()
    vendedores = [v['VENDEDOR'] for v in vendedores_data]
    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado para esta loja.")
        if st.button("↩️ Voltar", key="btn_voltar_venda"):
            st.session_state.etapa = 'atendimento'
            st.rerun()
        return

    # Seleciona vendedor
    vendedor = st.selectbox(
        "Vendedor",
        vendedores,
        index=None,
        placeholder="Selecione o vendedor",
        key="vend_venda"
    )

    # Cliente
    cliente = st.text_input("Nome do Cliente", key="cliente_venda_input")
    cliente = cliente.strip().upper()

    # === ESCOLHA DE TIPO: VENDA, PERDA OU RESERVA ===
    st.markdown("### 🔘 Selecione o tipo de registro:")
    cols = st.columns(3)

    with cols[0]:
        if st.button("✅ VENDA", use_container_width=True, type="primary", key="btn_tipo_venda"):
            st.session_state.tipo_registro = "VENDA"
            st.session_state.cliente_venda = cliente
            st.session_state.vendedor_venda = vendedor
            st.rerun()

    with cols[1]:
        if st.button("❌ PERDA", use_container_width=True, type="secondary", key="btn_tipo_perda"):
            st.session_state.tipo_registro = "PERDA"
            st.session_state.cliente_venda = cliente
            st.session_state.vendedor_venda = vendedor
            st.rerun()

    with cols[2]:
        if st.button("🗓️ RESERVA", use_container_width=True, type="secondary", key="btn_tipo_reserva"):
            st.session_state.tipo_registro = "RESERVA"
            st.session_state.cliente_venda = cliente
            st.session_state.vendedor_venda = vendedor
            st.rerun()

    # Verifica se o tipo foi escolhido
    if 'tipo_registro' not in st.session_state:
        st.warning("⚠️ Por favor, escolha o tipo de registro acima.")
        return

    # === MOSTRA CONFIRMAÇÃO DO TIPO ESCOLHIDO ===
    tipo = st.session_state.tipo_registro
    cli = st.session_state.cliente_venda
    vend = st.session_state.vendedor_venda

    st.markdown("---")
    st.success(f"✅ **CONFIRMADO**: {cli} | **Tipo:** {tipo} | Vendedor: {vend}")

    # Botão para confirmar e registrar
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↩️ VOLTAR", use_container_width=True, key="btn_voltar_venda_2"):
            if 'tipo_registro' in st.session_state:
                del st.session_state.tipo_registro
            if 'cliente_venda' in st.session_state:
                del st.session_state.cliente_venda
            if 'vendedor_venda' in st.session_state:
                del st.session_state.vendedor_venda
            st.session_state.etapa = 'atendimento'
            st.rerun()

    with col2:
        if st.button("✅ CONFIRMAR", type="primary", use_container_width=True, key="btn_registrar_venda"):
            if not vendedor or not cliente or "tipo_registro" not in st.session_state:
                st.error("⚠️ Preencha todos os campos!")
            else:
                dados = {
                    'loja': st.session_state.loja,
                    'vendedor': vendedor,
                    'cliente': cliente,
                    'data': datetime.now().strftime("%d/%m/%Y"),
                    'atendimento': '1',
                    'receita': '1',
                    'venda': '1' if st.session_state.tipo_registro == "VENDA" else '',
                    'perda': '1' if st.session_state.tipo_registro == "PERDA" else '',
                    'reserva': '1' if st.session_state.tipo_registro == "RESERVA" else '',
                    'pesquisa': '',
                    'consulta': '',
                    'hora': datetime.now().strftime("%H:%M")
                }
                if gsheets.registrar_atendimento(dados):
                    st.balloons()
                    st.success("✅ Registro salvo com sucesso!")
                    # Limpa os dados confirmados
                    del st.session_state.tipo_registro
                    del st.session_state.cliente_venda
                    del st.session_state.vendedor_venda
                    st.session_state.etapa = 'loja'
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar no Google Sheets.")