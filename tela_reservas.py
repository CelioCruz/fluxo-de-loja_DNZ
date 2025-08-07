import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_reservas():
    st.subheader("📦 RESERVAS ACUMULADAS")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Atendente:** {st.session_state.nome_atendente}")
    st.markdown("---")

    if 'gsheets' not in st.session_state:
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    # Carrega vendedores
    vendedores_data = gsheets.get_vendedores_por_loja()
    vendedores = [v['VENDEDOR'] for v in vendedores_data]
    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
        if st.button("↩️ Voltar", key="btn_voltar_reservas"):
            st.session_state.etapa = 'atendimento'
            st.rerun()
        return

    # Seleciona vendedor
    vendedor = st.selectbox(
        "Vendedor",
        vendedores,
        index=None,
        placeholder="Selecione o vendedor",
        key="vend_reservas"
    )

    # Cliente
    cliente = st.text_input("Nome do Cliente", key="cliente_reservas_input")
    cliente = cliente.strip().upper()

    # === ESCOLHA DE TIPO: CONVERSÃO OU DESISTÊNCIA ===
    st.markdown("### 🔘 Selecione o tipo de registro:")

    cols = st.columns(2)

    with cols[0]:
        if st.button("✅ CONVERSÃO", use_container_width=True, type="primary", key="btn_tipo_venda"):
            st.session_state.tipo_reserva = "CONVERSÃO"
            st.session_state.cliente_reserva = cliente
            st.session_state.vendedor_reserva = vendedor
            st.rerun()

    with cols[1]:
        if st.button("❌ DESISTÊNCIA", use_container_width=True, type="secondary", key="btn_tipo_perda"):
            st.session_state.tipo_reserva = "DESISTÊNCIA"
            st.session_state.cliente_reserva = cliente
            st.session_state.vendedor_reserva = vendedor
            st.rerun()

    # Verifica se o tipo foi escolhido
    if 'tipo_reserva' not in st.session_state:
        st.warning("⚠️ Por favor, escolha o tipo de registro acima.")
        return

    # === MOSTRA CONFIRMAÇÃO DO TIPO ESCOLHIDO ===
    tipo = st.session_state.tipo_reserva
    cli = st.session_state.cliente_reserva
    vend = st.session_state.vendedor_reserva

    st.markdown("---")
    st.success(f"✅ **CONFIRMADO**: {cli} | **Tipo:** {tipo} | Vendedor: {vend}")

    # Botão para confirmar e registrar
    if st.button("✅ REGISTRAR RESERVA", type="primary", use_container_width=True, key="btn_registrar_reserva"):
        if not vendedor or not cliente:
            st.error("⚠️ Preencha todos os campos!")
        else:
            # Busca todos os registros do cliente na loja
            registros = gsheets.buscar_cliente_por_nome_e_loja(cliente, st.session_state.loja)

            if not registros:
                st.error(f"❌ Nenhum registro encontrado para **{cliente}** nesta loja.")
                return

            # Soma os valores de 'reserva' (soma líquida)
            soma_reservas = 0
            for row in registros:
                val = row.get('reserva', '0')
                try:
                    soma_reservas += int(val)
                except:
                    pass  # Ignora se não for número

            if soma_reservas < 1:
                st.error(f"❌ Esse cliente não tem reserva ativa.")
                return

            # Prepara os dados conforme o tipo
            if st.session_state.tipo_reserva == "CONVERSÃO":
                dados = {
                    'loja': st.session_state.loja,
                    'atendente': st.session_state.nome_atendente,
                    'vendedor': vendedor,
                    'cliente': cliente,
                    'data': datetime.now().strftime("%d/%m/%Y"),
                    'atendimento': '1',
                    'receita': '',
                    'venda': '1',
                    'perda': '',
                    'reserva': '-1',
                    'pesquisa': '',
                    'gar_lente': '',
                    'gar_armacao': '',
                    'ajuste': '',
                    'entrega': '',
                    'consulta': '',
                    'hora': datetime.now().strftime("%H:%M")
                }
            else:  # DESISTÊNCIA
                dados = {
                    'loja': st.session_state.loja,
                    'vendedor': vendedor,
                    'cliente': cliente,
                    'data': datetime.now().strftime("%d/%m/%Y"),
                    'reserva': '-1',
                    'hora': datetime.now().strftime("%H:%M")
                }

            # Salva no Google Sheets
            if gsheets.registrar_atendimento(dados):
                st.balloons()
                st.success("✅ Reserva consumida com sucesso!")
                # Limpa os dados confirmados
                del st.session_state.tipo_reserva
                del st.session_state.cliente_reserva
                del st.session_state.vendedor_reserva
                st.session_state.etapa = 'atendimento'
                st.rerun()
            else:
                st.error("❌ Falha ao salvar no Google Sheets.")

    # Botão Voltar
    if st.button("↩️ VOLTAR", use_container_width=True, key="btn_voltar_reservas_2"):
        if 'tipo_reserva' in st.session_state:
            del st.session_state.tipo_reserva
        if 'cliente_reserva' in st.session_state:
            del st.session_state.cliente_reserva
        if 'vendedor_reserva' in st.session_state:
            del st.session_state.vendedor_reserva
        st.session_state.etapa = 'atendimento'
        st.rerun()