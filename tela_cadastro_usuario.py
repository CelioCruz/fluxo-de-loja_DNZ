import streamlit as st
import json
import bcrypt
import os

def mostrar():
    st.title("👥 GERENCIAMENTO DE USUÁRIOS")
    
    # Carregar usuários existentes
    try:
        with open("usuarios.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            usuarios_list = dados.get("usuarios", [])
    except Exception as e:
        st.error(f"❌ Erro ao carregar usuários: {e}")
        usuarios_list = []

    # Seção para listar usuários cadastrados
    st.subheader("📋 Usuários Cadastrados")
    for u in usuarios_list:
        st.text(f"👤 {u['nome']}")

    st.divider()

    # Seção para cadastrar novo usuário/loja
    st.subheader("➕ Cadastrar Novo Usuário/Loja")
    nova_loja = st.text_input("Nome da Loja/Usuário (Ex: LOJA09)").upper()
    nova_senha = st.text_input("Senha", type="password")

    if st.button("💾 SALVAR CADASTRO", use_container_width=True):
        if not nova_loja or not nova_senha:
            st.warning("⚠️ Preencha todos os campos!")
        else:
            # Verificar se já existe
            if any(u['nome'].upper() == nova_loja for u in usuarios_list):
                st.error("❌ Usuário já cadastrado!")
            else:
                # Gerar hash da senha
                senha_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
                
                # Adicionar novo usuário
                usuarios_list.append({
                    "nome": nova_loja,
                    "senha_hash": senha_hash
                })
                
                # Salvar no arquivo
                try:
                    with open("usuarios.json", "w", encoding="utf-8") as f:
                        json.dump({"usuarios": usuarios_list}, f, indent=4)
                    st.success(f"✅ Usuário {nova_loja} cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")

    if st.button("↩️ VOLTAR", use_container_width=True):
        st.session_state.etapa = 'atendimento'
        st.rerun()
