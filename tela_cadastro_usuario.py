import streamlit as st
import json
import bcrypt
import os

def mostrar():
    st.title("👥 GERENCIAMENTO DE ACESSOS")
    
    # Carregar usuários existentes
    try:
        if os.path.exists("usuarios.json"):
            with open("usuarios.json", "r", encoding="utf-8") as f:
                dados = json.load(f)
                usuarios_list = dados.get("usuarios", [])
        else:
            usuarios_list = []
    except Exception as e:
        st.error(f"❌ Erro ao carregar usuários: {e}")
        usuarios_list = []

    # --- 1. SEÇÃO: ALTERAR SENHA (Apenas para nomes, não para LOJA) ---
    st.subheader("🔑 Alterar Senha de Administradores/Vendedores")
    # Filtra apenas usuários que não começam com LOJA
    usuarios_nomes = [u['nome'] for u in usuarios_list if not u['nome'].upper().startswith("LOJA")]
    
    if usuarios_nomes:
        col_u, col_p = st.columns([1, 1])
        u_sel = col_u.selectbox("Selecione o Usuário", usuarios_nomes, key="sel_user_change")
        nova_p = col_p.text_input("Nova Senha", type="password", key="change_pwd_input")
        
        if st.button("🔄 ATUALIZAR SENHA", use_container_width=True):
            if nova_p:
                for u in usuarios_list:
                    if u['nome'] == u_sel:
                        u['senha_hash'] = bcrypt.hashpw(nova_p.encode(), bcrypt.gensalt()).decode()
                        break
                try:
                    with open("usuarios.json", "w", encoding="utf-8") as f:
                        json.dump({"usuarios": usuarios_list}, f, indent=4)
                    st.success(f"✅ Senha de {u_sel} atualizada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")
            else:
                st.warning("⚠️ Informe a nova senha.")
    else:
        st.info("Nenhum usuário (nome) encontrado para alteração de senha.")

    st.divider()

    # --- 2. SEÇÃO: CADASTRAR NOVO ACESSO (Usuário ou Loja) ---
    st.subheader("➕ Cadastrar Novo Acesso")
    tipo = st.radio("O que deseja cadastrar?", ["Usuário (Nome)", "Loja"], horizontal=True)
    
    if tipo == "Loja":
        col1, col2 = st.columns(2)
        num_loja = col1.text_input("Número da Loja (Ex: 09)")
        # Remove espaços e garante o formato LOJAXX
        num_limpo = num_loja.replace(" ", "").upper()
        if num_limpo.startswith("LOJA"):
            nova_loja_nome = num_limpo
        else:
            nova_loja_nome = f"LOJA{num_limpo.zfill(2)}" if num_limpo else ""
        
        if nova_loja_nome:
            col2.info(f"O usuário de login será: **{nova_loja_nome}**")
    else:
        nova_loja_nome = st.text_input("Nome do Usuário (Ex: MARCOS)").upper().strip()

    nova_senha = st.text_input("Senha para o novo acesso", type="password", key="new_user_pwd")

    if st.button("💾 SALVAR NOVO CADASTRO", use_container_width=True):
        if not nova_loja_nome or not nova_senha:
            st.warning("⚠️ Preencha o nome/número e a senha!")
        else:
            if any(u['nome'].upper() == nova_loja_nome.upper() for u in usuarios_list):
                st.error(f"❌ O acesso '{nova_loja_nome}' já está cadastrado!")
            else:
                # Gerar hash da senha
                senha_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
                
                # Adicionar novo usuário
                usuarios_list.append({
                    "nome": nova_loja_nome.upper(),
                    "senha_hash": senha_hash
                })
                
                # Salvar no arquivo
                try:
                    with open("usuarios.json", "w", encoding="utf-8") as f:
                        json.dump({"usuarios": usuarios_list}, f, indent=4)
                    st.success(f"✅ {nova_loja_nome} cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {e}")

    st.divider()
    
    # --- 3. SEÇÃO: LISTAGEM ---
    with st.expander("📋 Ver Lista de Acessos Cadastrados"):
        col_list1, col_list2 = st.columns(2)
        
        # Separar usuários de lojas para melhor visualização
        adm_users = [u['nome'] for u in usuarios_list if not u['nome'].upper().startswith("LOJA")]
        loja_users = [u['nome'] for u in usuarios_list if u['nome'].upper().startswith("LOJA")]
        
        with col_list1:
            st.markdown("**👤 Usuários/Vendedores**")
            for u in sorted(adm_users):
                st.text(f"• {u}")
                
        with col_list2:
            st.markdown("**🏪 Lojas**")
            for u in sorted(loja_users):
                st.text(f"• {u}")

    if st.button("↩️ VOLTAR", use_container_width=True):
        st.session_state.etapa = 'atendimento'
        st.rerun()
