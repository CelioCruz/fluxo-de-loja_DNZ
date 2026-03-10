import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google_planilha import GooglePlanilha  

def tela_sem_receita():
    st.subheader("🔄 RETORNO SEM RESERVA")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    if 'gsheets' not in st.session_state:
        try:
            st.session_state.gsheets = GooglePlanilha()
        except Exception as e:
            st.error("❌ Falha ao conectar com Google Sheets")
            st.exception(e)
            return
    gsheets = st.session_state.gsheets

    # Carregar vendedores
    try:
        vendedores_data = gsheets.get_vendedores_por_loja()
        vendedores = [v['VENDEDOR'] for v in vendedores_data] if vendedores_data else []
    except Exception as e:
        st.error(f"❌ Erro ao carregar vendedores: {e}")
        vendedores = []

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
                # ✅ Usa horário de São Paulo
                horario_sp = datetime.now(ZoneInfo("America/Sao_Paulo"))
                st.session_state.retorno_confirmado = {
                    'vendedor': vendedor,
                    'cliente': cliente,
                    'data': horario_sp.strftime("%d/%m/%Y"),
                    'hora': horario_sp.strftime("%H:%M")
                }

    with col2:
        if st.button("↩️ VOLTAR", key="btn_voltar_retorno_2"):
            st.session_state.etapa = 'atendimento'
            if 'retorno_confirmado' in st.session_state:
                del st.session_state.retorno_confirmado
            st.rerun()

    # Mostra a confirmação persistente (se houver)
    if "retorno_confirmado" in st.session_state:
        conf = st.session_state.retorno_confirmado
        st.markdown("---")
        st.success(f"✅ **CONFIRMADO**: {conf['cliente']} | Vendedor: {conf['vendedor']}")

        # ✅ VALIDAÇÃO: Verifica se o cliente teve 'perda = 1' nos últimos 30 dias
        if st.button("💾 Registrar no Sistema", type="secondary", key="btn_salvar_retorno"):
            if not conf['vendedor'] or not conf['cliente']:
                st.error("⚠️ Dados incompletos!")
                return

            try:
                # ✅ Horário de São Paulo
                horario_sp = datetime.now(ZoneInfo("America/Sao_Paulo"))

                # ✅ Tudo certo: registrar
                dados = {
                    'loja': st.session_state.loja,
                    'vendedor': conf['vendedor'],
                    'cliente': conf['cliente'],
                    'data': horario_sp.strftime("%d/%m/%Y"),
                    'hora': horario_sp.strftime("%H:%M"),
                    'atendimento': '1',
                    'receita': '',
                    'venda': '1',
                    'perda': '-1', 
                    'reserva': '',
                    'pesquisa': '',
                    'exame': '',  
                }

                if gsheets.registrar_atendimento(dados):
                    st.balloons()
                    st.success("✅ Retorno registrado com sucesso!")
                    del st.session_state.retorno_confirmado
                    st.session_state.etapa = 'atendimento'
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar na planilha.")

            except Exception as e:
                st.error(f"❌ Erro ao verificar histórico de perda ou salvar: {e}")