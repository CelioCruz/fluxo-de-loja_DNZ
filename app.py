import streamlit as st
import sys
import os
import base64
import json
import bcrypt
from datetime import datetime
import importlib
import logging

# 🔥 Garante que o diretório do app.py esteja no sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ✅ Inicialização do estado
if 'etapa' not in st.session_state: st.session_state.etapa = 'login'
if 'loja' not in st.session_state: st.session_state.loja = ''
if 'subtela' not in st.session_state: st.session_state.subtela = ''
if 'nome_atendente' not in st.session_state: st.session_state.nome_atendente = ''
if 'horario_entrada' not in st.session_state: st.session_state.horario_entrada = None

st.set_page_config(page_title="Fluxo de Loja", layout="centered")

def set_fundo_cor_solido():
    st.markdown("<style>.stApp { background-color: #f0f4e2; }</style>", unsafe_allow_html=True)
set_fundo_cor_solido()

def garantir_conexao_gsheets():
    if 'gsheets' not in st.session_state:
        from google_planilha import GooglePlanilha
        st.session_state.gsheets = GooglePlanilha()

def tela_login():
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🔐 ACESSO AO SISTEMA</h1>", unsafe_allow_html=True)
    try:
        with open("usuarios.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            usuarios = {u["nome"].upper(): u for u in dados["usuarios"]}
    except:
        st.error("❌ Erro ao carregar usuários.")
        return

    nome = st.text_input("Usuário").upper()
    senha = st.text_input("Senha", type="password")

    if st.button("✅ ENTRAR NO SISTEMA", use_container_width=True):
        if nome in usuarios and bcrypt.checkpw(senha.encode(), usuarios[nome]["senha_hash"].encode()):
            st.session_state.nome_atendente = nome
            st.session_state.etapa = 'loja'
            st.session_state.horario_entrada = datetime.now()
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")

# --- Navegação ---
if st.session_state.etapa == 'login':
    tela_login()

elif st.session_state.etapa == 'loja':
    garantir_conexao_gsheets()
    from selecionar_loja import tela_selecao_loja
    tela_selecao_loja()

elif st.session_state.etapa == 'atendimento':
    garantir_conexao_gsheets()
    from tela_atendimento import tela_atendimento_principal
    tela_atendimento_principal()

elif st.session_state.etapa == 'subtela':
    garantir_conexao_gsheets()
    nome_modulo = f"tela_{st.session_state.subtela}"
    try:
        module = importlib.import_module(nome_modulo)
        func = getattr(module, 'mostrar', None) or getattr(module, nome_modulo, None)
        if func: func()
        else: st.error(f"❌ Erro no módulo {nome_modulo}")
    except Exception as e:
        st.error(f"❌ Erro ao carregar {nome_modulo}: {e}")

# Sidebar
if st.session_state.nome_atendente:
    st.sidebar.markdown(f"**👤 Atendente:** {st.session_state.nome_atendente}")
    st.sidebar.markdown(f"**🏪 Loja:** {st.session_state.loja}")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()
