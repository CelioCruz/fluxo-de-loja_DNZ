import streamlit as st

def tela_atendimento_principal():
    st.title("💼 TELA DE ATENDIMENTO")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")  # Corrigido para linha completa

    # === LISTA DE BOTÕES ===
    botoes = [
        ("💊 Atendimento com Receita", "venda_receita"),
        ("📌 Reservas Acumuladas", "reservas"),
        ("🔄 Retorno sem Reserva", "sem_receita"),
        ("🔍 Atendimento sem Receita", "pesquisa"),
        ("📅 Exame de Vista", "consulta"),
        ("📊 Relatório por Vendedor", "relatorio_vendedor")  
    ]

    # Exibe os botões em pares (2 por linha)
    for i in range(0, len(botoes), 2):
        cols = st.columns(2)
        btn1_texto, btn1_chave = botoes[i]
        
        with cols[0]:
            if st.button(btn1_texto, use_container_width=True, key=f"btn_{btn1_chave}"):
                st.session_state.subtela = btn1_chave
                st.session_state.etapa = 'subtela'
                st.rerun()

        # Segundo botão (se existir)
        if i + 1 < len(botoes):
            btn2_texto, btn2_chave = botoes[i + 1]
            with cols[1]:
                if st.button(btn2_texto, use_container_width=True, key=f"btn_{btn2_chave}"):
                    st.session_state.subtela = btn2_chave
                    st.session_state.etapa = 'subtela'
                    st.rerun()

    st.markdown("---")

    # Botão de voltar
    if st.button("🚪 VOLTAR", use_container_width=True, type="secondary"):
        st.session_state.etapa = 'loja'
        st.session_state.loja = ''
        st.session_state.subtela = ''
        st.rerun()