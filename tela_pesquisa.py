import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_pesquisa():
    st.subheader("🔍 PESQUISA SEM RECEITA")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    if 'gsheets' not in st.session_state:
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    # Carregar vendedores
    vendedores_data = gsheets.get_vendedores_por_loja()
    vendedores = [v['VENDEDOR'] for v in vendedores_data]

    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado para esta loja.")
        if st.button("↩️ Voltar", key="btn_voltar_pesquisa"):
            st.session_state.etapa = 'atendimento'
            st.rerun()
        return

    # Seleção de vendedor
    vendedor = st.selectbox(
        "Vendedor",
        vendedores,
        index=None,
        placeholder="Selecione o vendedor",
        key="vend_pesquisa"
    )

    # Nome do cliente
    cliente = st.text_input("Nome do Cliente", key="cliente_pesquisa_input")
    cliente = cliente.strip().upper()

    # === REGISTRO DO TIPO: PESQUISA (único tipo aqui) ===
    # Como só tem um tipo, vamos confirmar direto
    if st.button("✅ CONFIRMAR", type="primary", key="btn_registrar_pesquisa"):
        if not vendedor or not cliente:
            st.error("⚠️ Preencha todos os campos!")
        else:
            # Armazena no session_state para exibir "CONFIRMADO"
            st.session_state.tipo_registro = "PESQUISA"
            st.session_state.cliente_pesquisa = cliente
            st.session_state.vendedor_pesquisa = vendedor
            st.rerun()

    # Mostra a confirmação se já foi feita
    if 'tipo_registro' in st.session_state and st.session_state.tipo_registro == "PESQUISA":
        cliente_conf = st.session_state.cliente_pesquisa
        vendedor_conf = st.session_state.vendedor_pesquisa
        st.markdown("---")
        st.success(f"✅ **CONFIRMADO**: {cliente_conf} | **Tipo:** PESQUISA | Vendedor: {vendedor_conf}")

        # Confirmação final e registro
        if st.button("💾 REGISTRAR PESQUISA", type="primary", use_container_width=True, key="btn_salvar_pesquisa"):
            dados = {
                'loja': st.session_state.loja,
                'atendente': st.session_state.nome_atendente,
                'vendedor': vendedor_conf,
                'cliente': cliente_conf,
                'data': datetime.now().strftime("%d/%m/%Y"),
                'atendimento': '1',
                'receita': '',
                'venda': '',
                'perda': '',
                'reserva': '',
                'pesquisa': '1',
                'consulta': '',
                'hora': datetime.now().strftime("%H:%M")
            }
            if gsheets.registrar_atendimento(dados):
                st.balloons()
                st.success("✅ Pesquisa registrada com sucesso!")
                # Limpa o estado
                del st.session_state.tipo_registro
                del st.session_state.cliente_pesquisa
                del st.session_state.vendedor_pesquisa
                st.session_state.etapa = 'loja'
                st.rerun()
            else:
                st.error("❌ Falha ao salvar na planilha.")

    # Botão Voltar
    if st.button("↩️ VOLTAR", key="btn_voltar_pesquisa_2"):
        if 'tipo_registro' in st.session_state:
            del st.session_state.tipo_registro
            del st.session_state.cliente_pesquisa
            del st.session_state.vendedor_pesquisa
        st.session_state.etapa = 'atendimento'
        st.rerun()