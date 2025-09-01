import streamlit as st
from datetime import datetime
from google_planilha import GooglePlanilha

def tela_sem_receita():
    st.subheader("🔄 RETORNO SEM RESERVA")
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
        if st.button("↩️ VOLTAR", key="btn_voltar_retorno"):
            st.session_state.etapa = 'atendimento'
            st.rerun()
        return

    # Seleção de vendedor
    vendedor = st.selectbox(
        "Vendedor", 
        vendedores, 
        index=None, 
        placeholder="Selecione um vendedor", 
        key="vend_retorno"
    )

    # Nome do cliente
    cliente = st.text_input("Nome do Cliente", key="cliente_retorno_input")
    cliente = cliente.strip().upper()

    # Botões de ação
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ CONFIRMAR", type="primary", key="btn_registrar_retorno"):
            if not vendedor or not cliente:
                st.error("⚠️ Preencha todos os campos!")
            else:
                # Salva os dados confirmados no session_state
                st.session_state.retorno_confirmado = {
                    'vendedor': vendedor,
                    'cliente': cliente,
                    'data': datetime.now().strftime("%d/%m/%Y"),
                    'hora': datetime.now().strftime("%H:%M")
                }
                
    with col2:
        if st.button("↩️ VOLTAR", key="btn_voltar_retorno_2"):
            st.session_state.etapa = 'atendimento'
            # Limpa a confirmação ao voltar (opcional)
            if 'retorno_confirmado' in st.session_state:
                del st.session_state.retorno_confirmado
            st.rerun()

    # Mostra a confirmação persistente (se houver)
    if "retorno_confirmado" in st.session_state:
        conf = st.session_state.retorno_confirmado
        st.markdown("---")
        st.success(f"✅ **CONFIRMADO**: {conf['cliente']} | Vendedor: {conf['vendedor']}")

        # Opção de registrar no Google Sheets
        if st.button("💾 Registrar no Sistema ", type="secondary", key="btn_salvar_retorno"):
            dados = {
                'loja': st.session_state.loja,
                'atendente': st.session_state.nome_atendente,
                'vendedor': conf['vendedor'],
                'cliente': conf['cliente'],
                'data': conf['data'],
                'atendimento': '1',
                'receita': '',
                'venda': '1',
                'perda': '-1',
                'reserva': '',
                'pesquisa': '',
                'consulta': '',
                'hora': conf['hora']
            }
            if gsheets.registrar_atendimento(dados):
                st.balloons()
                st.success("✅ Dados enviados para a planilha!")
                # Limpa após salvar
                del st.session_state.retorno_confirmado
                st.session_state.etapa = 'loja'
                st.rerun()
            else:
                st.error("❌ Falha ao salvar na planilha.")