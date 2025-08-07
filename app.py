import streamlit as st
import base64
import json
import bcrypt

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Loja", layout="centered")


# --- FUNÇÃO PARA FUNDO ---
def set_fundo_cor_solido():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f0f4e2;  
            background-image: none;     
        }
        </style>
        """,
        unsafe_allow_html=True
    )


set_fundo_cor_solido()


# --- ESTADO INICIAL ---
if 'etapa' not in st.session_state:
    st.session_state.etapa = 'login'  # Agora começa no login
if 'loja' not in st.session_state:
    st.session_state.loja = ''
if 'subtela' not in st.session_state:
    st.session_state.subtela = ''


# --- TELA DE LOGIN ---
def tela_login():
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🔐 ACESSO AO SISTEMA</h1>", unsafe_allow_html=True)
    st.subheader("Autenticação de Usuário")

    # Carregar usuários
    try:
        with open("usuarios.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            usuarios = {u["nome"].upper(): u for u in dados["usuarios"]}
    except FileNotFoundError:
        st.error("❌ Arquivo de usuários não encontrado. Contate o administrador.")
        return
    except Exception as e:
        st.error(f"❌ Erro ao carregar usuários: {str(e)}")
        return

    # Formulário de login
    nome = st.text_input("Usuário").upper()
    senha = st.text_input("Senha", type="password")

    if st.button("✅ ENTRAR NO SISTEMA", use_container_width=True):
        if nome in usuarios:
            usuario = usuarios[nome]
            senha_hash = usuario["senha_hash"].encode()
            if bcrypt.checkpw(senha.encode(), senha_hash):
                st.session_state.nome_atendente = nome
                st.session_state.etapa = 'loja'  # Vai direto para seleção de loja
                st.success(f"✅ Bem-vindo, {nome}!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
        else:
            st.error("❌ Usuário não encontrado.")

    # Botão: Fechar Sistema
    if st.button("❌ FECHAR SISTEMA", use_container_width=True, type="secondary"):
        # Mostra mensagem e instrui o usuário a fechar a aba
        st.markdown("### 🖐️ Sistema encerrado")
        st.info("Você pode fechar esta aba ou janela do navegador.")
        st.stop()  # Para a execução do Streamlit

# --- CARREGAMENTO DAS TELAS PRINCIPAIS ---
try:
    from selecionar_loja import tela_selecao_loja
except Exception as e:
    st.error("Falha ao carregar selecionar_loja.py")
    st.code(str(e))
try:
    from tela_atendimento import tela_atendimento_principal
except Exception as e:
    st.error("Falha ao carregar tela_atendimento.py")
    st.code(str(e))

# Subtelas
SUBTELAS = {}
for nome in [
    'tela_venda_receita', 'tela_pesquisa', 'tela_consulta',
    'tela_reservas', 'tela_sem_receita', 'tela_encaminhamento',
]:
    try:
        exec(f"from {nome} import {nome.replace('-', '_')}")
        SUBTELAS[nome.replace('tela_', '').replace('retorno_', '')] = eval(nome.replace('-', '_'))
    except Exception as e:
        def erro(): st.error(f"❌ {nome}")
        SUBTELAS[nome.replace('tela_', '')] = erro

# === NAVEGAÇÃO ENTRE TELAS ===
if st.session_state.etapa == 'login':
    tela_login()
elif st.session_state.etapa == 'loja':
    tela_selecao_loja()
elif st.session_state.etapa == 'atendimento':
    tela_atendimento_principal()
elif st.session_state.etapa == 'subtela':
    if st.session_state.subtela in SUBTELAS:
        SUBTELAS[st.session_state.subtela]()
    else:
        st.error("Tela não encontrada")
        if st.button("Voltar", key="btn_voltar_geral"):
            st.session_state.etapa = 'loguin'
            st.rerun()
else:
    st.error("Etapa inválida.")
    st.session_state.etapa = 'login'
    st.rerun()   

# Rodapé
st.markdown("<br><hr><center><small>💼 Projeto <strong>Leonardo Pesil, desenvolvido por Cruz.devsoft</strong> | © 2025</small></center>", unsafe_allow_html=True)