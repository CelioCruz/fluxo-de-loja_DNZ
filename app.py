# app.py

import streamlit as st
import base64
import json
import bcrypt
from datetime import datetime
from zoneinfo import ZoneInfo  # Para fuso horário

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
    st.session_state.etapa = 'login'
if 'loja' not in st.session_state:
    st.session_state.loja = ''
if 'subtela' not in st.session_state:
    st.session_state.subtela = ''
if 'nome_atendente' not in st.session_state:
    st.session_state.nome_atendente = ''
if 'horario_entrada' not in st.session_state:
    st.session_state.horario_entrada = None
if 'horario_saida' not in st.session_state:
    st.session_state.horario_saida = None


# 🔹 Função global: atualiza reservas expiradas
def atualizar_reservas():
    """Executa limpeza de reservas antigas. Deve ser chamada após ter gsheets."""
    try:
        if 'gsheets' in st.session_state:
            # Use minutos=1 para testes, depois mude para 72*60
            count = st.session_state.gsheets.limpar_reservas_antigas(minutos=72*60) # expira após 72 horas
            if count > 0:
                st.toast(f"✅ {count} reserva(s) expirada(s) removida(s).", icon="🧹")
    except Exception as e:
        st.error(f"❌ Erro ao limpar reservas: {str(e)}")


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
                st.session_state.etapa = 'loja'
                st.session_state.horario_entrada = datetime.now()
                st.success(f"✅ Bem-vindo, {nome}!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
        else:
            st.error("❌ Usuário não encontrado.")

    # Botão: Fechar Sistema
    if st.button("❌ FECHAR SISTEMA", use_container_width=True, type="secondary"):
        st.session_state.horario_saida = datetime.now()
        st.markdown("### 🖐️ Sessão encerrada")
        entrada = st.session_state.horario_entrada.strftime("%d/%m/%Y às %H:%M:%S") if st.session_state.horario_entrada else "Não registrado"
        saida = st.session_state.horario_saida.strftime("%d/%m/%Y às %H:%M:%S")
        st.info(f"**Entrada:** {entrada}\n\n**Saída:** {saida}")
        st.success("Obrigado por usar o sistema! Você pode fechar a aba.")
        st.stop()


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
    'tela_reservas', 'tela_sem_receita', 'tela_encaminhamento', 'tela_lente',
]:
    try:
        module_name = nome.replace('-', '_')
        exec(f"from {nome} import {module_name}")
        SUBTELAS[nome.replace('tela_', '').replace('retorno_', '')] = eval(module_name)
    except Exception as e:
        def erro(): 
            st.error(f"❌ Falha ao carregar {nome}.py")
        SUBTELAS[nome.replace('tela_', '')] = erro


# === NAVEGAÇÃO ENTRE TELAS ===
if st.session_state.etapa == 'login':
    tela_login()

elif st.session_state.etapa == 'loja':
    # ✅ Conecta com Google Sheets
    if 'gsheets' not in st.session_state:
        try:
            from google_planilha import GooglePlanilha
            st.session_state.gsheets = GooglePlanilha()
        except Exception as e:
            st.error("❌ Falha ao conectar ao Google Sheets")
            st.exception(e)
            st.stop()

    # ✅ Atualiza reservas ANTES de carregar a tela
    atualizar_reservas()
    tela_selecao_loja()

elif st.session_state.etapa == 'atendimento':
    # ✅ Garante que gsheets está carregado
    if 'gsheets' not in st.session_state:
        try:
            from google_planilha import GooglePlanilha
            st.session_state.gsheets = GooglePlanilha()
        except Exception as e:
            st.error("❌ Falha ao conectar ao Google Sheets")
            st.exception(e)
            st.stop()

    # ✅ Atualiza reservas
    atualizar_reservas()
    tela_atendimento_principal()

elif st.session_state.etapa == 'subtela':
    # ✅ Garante que gsheets está carregado
    if 'gsheets' not in st.session_state:
        try:
            from google_planilha import GooglePlanilha
            st.session_state.gsheets = GooglePlanilha()
        except Exception as e:
            st.error("❌ Falha ao conectar ao Google Sheets")
            st.exception(e)
            st.stop()

    # ✅ Atualiza reservas
    atualizar_reservas()

    if st.session_state.subtela in SUBTELAS:
        SUBTELAS[st.session_state.subtela]()
    else:
        st.error("Tela não encontrada")
        if st.button("Voltar", key="btn_voltar_geral"):
            st.session_state.etapa = 'login'
            st.rerun()

else:
    st.error("Etapa inválida.")
    st.session_state.etapa = 'login'
    st.rerun()


# --- MOSTRAR HORÁRIO DE ENTRADA NO SIDEBAR OU TOPO ---
if st.session_state.horario_entrada:
    horario_formatado = st.session_state.horario_entrada.strftime("%H:%M:%S")
    st.sidebar.markdown(f"**🕒 Entrada:** {horario_formatado}")
    if st.session_state.nome_atendente:
        st.sidebar.markdown(f"**👤 Atendente:** {st.session_state.nome_atendente}")

# Rodapé
st.markdown(
    "<br><hr><center>"
    "<small>💼 Projeto <strong>Leonardo Pesil</strong>, desenvolvido por <strong>Cruz.devsoft</strong> | © 2025</small>"
    "</center>",
    unsafe_allow_html=True
)