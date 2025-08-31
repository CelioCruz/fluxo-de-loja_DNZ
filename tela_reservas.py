import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_reservas():
    st.subheader("📦 RESERVAS ACUMULADAS")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Atendente:** {st.session_state.nome_atendente}")
    st.markdown("---")

    # Inicializa ou usa a instância do GooglePlanilha
    if 'gsheets' not in st.session_state:
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    # Carrega vendedores
    try:
        vendedores_data = gsheets.get_vendedores_por_loja()
        vendedores = [v['VENDEDOR'] for v in vendedores_data]
    except Exception as e:
        st.error(f"Erro ao carregar vendedores: {e}")
        vendedores = []

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
    cliente_input = st.text_input("Nome do Cliente", key="cliente_reservas_input")
    cliente = cliente_input.strip().upper() if cliente_input else ""

    # === ESCOLHA DE TIPO: CONVERSÃO OU DESISTÊNCIA ===
    st.markdown("### 🔘 Selecione o tipo de registro:")

    cols = st.columns(2)

    with cols[0]:
        if st.button("✅ CONVERSÃO", use_container_width=True, type="primary", key="btn_tipo_venda"):
            if not vendedor or not cliente:
                st.error("Preencha o vendedor e o cliente!")
                return
            st.session_state.tipo_reserva = "CONVERSÃO"
            st.session_state.cliente_reserva = cliente
            st.session_state.vendedor_reserva = vendedor
            st.rerun()

    with cols[1]:
        if st.button("❌ DESISTÊNCIA", use_container_width=True, type="secondary", key="btn_tipo_perda"):
            if not vendedor or not cliente:
                st.error("Preencha o vendedor e o cliente!")
                return
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

    # Botão para registrar diretamente com -1
    if st.button("✅ REGISTRAR RESERVA", type="primary", use_container_width=True, key="btn_registrar_reserva"):
        if not vendedor or not cliente:
            st.error("⚠️ Preencha todos os campos!")
            return

        # ✅ Prepara o registro com -1 na reserva (sem validação)
        dados_registro = {
            'loja': st.session_state.loja,
            'atendente': st.session_state.nome_atendente,
            'vendedor': vendedor,
            'cliente': cliente,
            'data': datetime.now().strftime("%d/%m/%Y"),
            'hora': datetime.now().strftime("%H:%M"),
            'reserva': -1  # Marca consumo de reserva (direto, sem checar)
        }

        # Adiciona campos específicos por tipo
        if tipo == "CONVERSÃO":
            dados_registro['atendimento'] = '1'
            dados_registro['venda'] = '1'
            dados_registro['perda'] = ''
        else:  # DESISTÊNCIA
            dados_registro['atendimento'] = ''
            dados_registro['venda'] = ''
            dados_registro['perda'] = '1'

        # 📥 Salva no Google Sheets
        try:
            sucesso = gsheets.registrar_atendimento(dados_registro)
        except Exception as e:
            st.error(f"❌ Erro ao salvar: {e}")
            sucesso = False

        if sucesso:
            st.balloons()
            st.success("✅ Reserva registrada com sucesso! (-1)")
            # Limpa o estado
            del st.session_state.tipo_reserva
            del st.session_state.cliente_reserva
            del st.session_state.vendedor_reserva
            st.session_state.etapa = 'loja'
            st.rerun()
        else:
            st.error("❌ Falha ao salvar no Google Sheets.")

    # Botão Voltar
    if st.button("↩️ VOLTAR", use_container_width=True, key="btn_voltar_reservas_2"):
        for key in ['tipo_reserva', 'cliente_reserva', 'vendedor_reserva']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.etapa = 'loja'
        st.rerun()