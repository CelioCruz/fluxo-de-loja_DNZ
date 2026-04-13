import streamlit as st
import json
import os

def tela_selecao_loja():
    st.title("🏪 SELECIONE A LOJA")
    
    # Carregar lojas dinamicamente do usuarios.json
    lojas_exibicao = []
    try:
        if os.path.exists("usuarios.json"):
            with open("usuarios.json", "r", encoding="utf-8") as f:
                dados = json.load(f)
                # Busca usuários que começam com "LOJA"
                lojas_db = [u["nome"].upper() for u in dados["usuarios"] if u["nome"].upper().startswith("LOJA")]
                
                # Formata para exibição (ex: "LOJA01" -> "LOJA 01")
                for l in sorted(lojas_db):
                    if len(l) > 4 and l.startswith("LOJA"):
                        lojas_exibicao.append(f"LOJA {l[4:]}")
                    else:
                        lojas_exibicao.append(l)
    except Exception as e:
        st.error(f"Erro ao carregar lojas: {e}")

    # Fallback caso não encontre nenhuma no JSON
    if not lojas_exibicao:
        lojas_exibicao = [f"LOJA {str(i).zfill(2)}" for i in range(1, 9)]

    loja = st.selectbox("Selecione sua loja:", lojas_exibicao, index=0, key="loja_select")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ CONFIRMAR", use_container_width=True, key="btn_confirmar_loja"):
            st.session_state.loja = loja
            st.session_state.etapa = 'atendimento'
            st.rerun()
    with col2:
        if st.button("↩️ VOLTAR", use_container_width=True, key="btn_voltar_loja"):
            st.session_state.etapa = 'login' # Corrigido de 'loguin'
            st.rerun()
