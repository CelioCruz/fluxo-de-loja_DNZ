import streamlit as st

def tela_atendimento_principal():
    st.title("💼 TELA DE ATENDIMENTO")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Usuário:** {st.session_state.nome_atendente}")
    st.markdown("-") 
    # === BOTÕES PERSONALIZADOS COM CSS ===
    botoes = [
        ("💊 Atendimento com Receita", "venda_receita"),
        ("📌 Reservas Acumuladas", "reservas"),
        ("🔄 Retorno sem Reserva", "sem_receita"),
        ("🔍 Atendimento sem Receita", "pesquisa"),
        ("📅 Exame de Vista", "consulta"),
        ("📦 Reserva Lentes Prontas","lente")
    ]

    # Dividimos em pares: cada linha terá 2 botões
    for i in range(0, len(botoes), 2):
        col1, col2 = st.columns(2)
        btn_texto1, chave1 = botoes[i]
        btn_texto2, chave2 = botoes[i + 1] if i + 1 < len(botoes) else ("", "")

        with col1:
            if st.button(btn_texto1, use_container_width=True, key=f"btn_{chave1}"):
                st.session_state.subtela = chave1
                st.session_state.etapa = 'subtela'
                st.rerun()

        with col2:
            if btn_texto2:  # Evita erro se faltar botão na última linha
                if st.button(btn_texto2, use_container_width=True, key=f"btn_{chave2}"):
                    st.session_state.subtela = chave2
                    st.session_state.etapa = 'subtela'
                    st.rerun()

    st.markdown("-")

    # Botão de sair (pode ser estilizado também, mas usamos o do Streamlit)
    if st.button("🚪 VOLTAR", use_container_width=True, type="secondary"):
        st.session_state.etapa = 'loja'      
        st.session_state.loja = ''           
        st.session_state.subtela = ''        
        st.rerun()