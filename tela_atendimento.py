import streamlit as st

def tela_atendimento_principal():
    st.title("💼 TELA DE ATENDIMENTO")
    st.info(f"**Loja:** {st.session_state.loja} | **Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    # === LISTA DE BOTÕES (Adicionado o botão GOOGLE) ===
    botoes = [
        ("💊 Atendimento com Receita", "venda_receita"),
        ("📌 Reservas Acumuladas", "reservas"),
        ("🔄 Retorno sem Reserva", "sem_receita"),
        ("🔍 Atendimento sem Receita", "pesquisa"),
        ("📅 Exame de Vista", "consulta"),
        ("🌐 GOOGLE", "google_registro"),  # Novo botão
        ("📊 Relatório por Vendedor", "relatorio_vendedor")
    ]

    # Exibe os botões em colunas
    for i in range(0, len(botoes), 2):
        cols = st.columns(2)
        btn1_texto, btn1_chave = botoes[i]
        with cols[0]:
            if st.button(btn1_texto, use_container_width=True, key=f"btn_{btn1_chave}"):
                st.session_state.subtela = btn1_chave
                st.session_state.etapa = 'subtela'
                st.rerun()

        if i + 1 < len(botoes):
            btn2_texto, btn2_chave = botoes[i + 1]
            with cols[1]:
                if st.button(btn2_texto, use_container_width=True, key=f"btn_{btn2_chave}"):
                    st.session_state.subtela = btn2_chave
                    st.session_state.etapa = 'subtela'
                    st.rerun()

    st.markdown("---")
    if st.button("🚪 VOLTAR", use_container_width=True, type="secondary"):
        st.session_state.etapa = 'loja'
        st.rerun()
