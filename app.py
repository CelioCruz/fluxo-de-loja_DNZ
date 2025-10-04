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

# ✅ Inicialização do estado (só uma vez!)
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
if 'enc_cliente' not in st.session_state:
    st.session_state.enc_cliente = ''
if 'enc_telefone' not in st.session_state:
    st.session_state.enc_telefone = ''
if 'enc_nascimento' not in st.session_state:
    st.session_state.enc_nascimento = ''
if 'enc_vendedor' not in st.session_state:
    st.session_state.enc_vendedor = ''
if 'enc_tipo' not in st.session_state:
    st.session_state.enc_tipo = 'PARTICULAR'
if 'pdf_gerado' not in st.session_state:
    st.session_state.pdf_gerado = False

# --- Configurações iniciais ---
st.set_page_config(page_title="Fluxo de Loja", layout="centered")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# 🔹 Função: atualiza reservas expiradas
def atualizar_reservas():
    agora = datetime.now()
    ultima_execucao = st.session_state.get("ultima_limpeza_reservas", None)
    if ultima_execucao and (agora - ultima_execucao).total_seconds() < 60:
        return

    try:
        if 'gsheets' in st.session_state:
            count = st.session_state.gsheets.limpar_reservas_antigas(minutos=72*60)
            if count > 0:
                st.toast(f"✅ {count} reserva(s) expirada(s) removida(s).", icon="🧹")
        st.session_state.ultima_limpeza_reservas = agora
    except Exception as e:
        st.error(f"❌ Erro ao limpar reservas: {str(e)}")

# --- Tela de Login ---
def tela_login():
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🔐 ACESSO AO SISTEMA</h1>", unsafe_allow_html=True)
    st.subheader("Autenticação de Usuário")

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

    if st.button("❌ FECHAR SISTEMA", use_container_width=True, type="secondary"):
        st.session_state.horario_saida = datetime.now()
        st.markdown("### 🖐️ Sessão encerrada")
        entrada = st.session_state.horario_entrada.strftime("%d/%m/%Y às %H:%M:%S") if st.session_state.horario_entrada else "Não registrado"
        saida = st.session_state.horario_saida.strftime("%d/%m/%Y às %H:%M:%S")
        st.info(f"**Entrada:** {entrada}\n\n**Saída:** {saida}")
        st.success("Obrigado por usar o sistema! Você pode fechar a aba.")
        st.stop()

# --- Carregamento das telas principais ---
try:
    from selecionar_loja import tela_selecao_loja
except Exception as e:
    st.error("❌ Falha ao carregar selecionar_loja.py")
    st.exception(e)
    st.stop()

try:
    from tela_atendimento import tela_atendimento_principal
except Exception as e:
    st.error("❌ Falha ao carregar tela_atendimento.py")
    st.exception(e)
    st.stop()

# === Função: carrega subtela dinamicamente ===
def carregar_subtela(nome_subtela):
    nome_modulo = f"tela_{nome_subtela}"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    try:
        if nome_modulo in sys.modules:
            importlib.reload(sys.modules[nome_modulo])
        module = importlib.import_module(nome_modulo)

        # Procura pela função 'mostrar' (padrão)
        if hasattr(module, 'mostrar'):
            return module.mostrar
        # Fallback: função com nome do módulo
        if hasattr(module, nome_modulo):
            return getattr(module, nome_modulo)
        # Fallback: função sem prefixo
        if hasattr(module, nome_subtela):
            return getattr(module, nome_subtela)

        # Nenhuma função válida
        st.error(f"❌ Nenhuma função válida encontrada em `{nome_modulo}.py`")
        def erro():
            st.error(f"❌ Erro: função não encontrada em `{nome_modulo}.py`")
        return erro

    except ModuleNotFoundError:
        st.error(f"❌ Módulo não encontrado: `{nome_modulo}.py`")
        def erro():
            st.error(f"❌ Arquivo `{nome_modulo}.py` não encontrado.")
        return erro
    except Exception as e:
        logger.error(f"❌ Erro ao carregar {nome_modulo}: {e}")
        st.error(f"❌ Erro ao carregar `{nome_modulo}.py`: {str(e)}")
        def erro():
            st.error(f"❌ Erro interno ao carregar `{nome_modulo}.py`")
        return erro

# === Função: garantir conexão com Google Sheets ===
def garantir_conexao_gsheets():
    if 'gsheets' not in st.session_state:
        try:
            from google_planilha import GooglePlanilha
            st.session_state.gsheets = GooglePlanilha()
            logger.info("✅ Conexão com Google Sheets estabelecida.")
        except Exception as e:
            st.error("❌ Falha ao conectar ao Google Sheets")
            st.exception(e)
            st.stop()

# === Navegação principal ===
if st.session_state.etapa == 'login':
    tela_login()

elif st.session_state.etapa == 'loja':
    garantir_conexao_gsheets()
    atualizar_reservas()
    tela_selecao_loja()

elif st.session_state.etapa == 'atendimento':
    garantir_conexao_gsheets()
    atualizar_reservas()
    tela_atendimento_principal()

elif st.session_state.etapa == 'subtela':
    garantir_conexao_gsheets()
    atualizar_reservas()
    func_subtela = carregar_subtela(st.session_state.subtela)
    if func_subtela:
        func_subtela()
    else:
        st.error("❌ Tela não encontrada.")
        if st.button("Voltar ao início", key="btn_voltar_inicio"):
            st.session_state.etapa = 'login'
            st.rerun()

else:
    st.error("⚠️ Etapa inválida.")
    st.session_state.etapa = 'login'
    st.rerun()

# --- Sidebar ---
st.sidebar.title("🧭 Navegação")
if st.session_state.horario_entrada:
    horario_formatado = st.session_state.horario_entrada.strftime("%H:%M:%S")
    st.sidebar.markdown(f"**🕒 Entrada:** {horario_formatado}")
if st.session_state.nome_atendente:
    st.sidebar.markdown(f"**👤 Atendente:** {st.session_state.nome_atendente}")
if st.session_state.loja:
    st.sidebar.markdown(f"**🏪 Loja:** {st.session_state.loja}")

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
    st.session_state.horario_saida = datetime.now()
    st.session_state.clear()
    st.rerun()

# --- Rodapé ---
st.markdown(
    "<br><hr><center>"
    "<small>💼 Projeto <strong>Leonardo Pesil</strong>, desenvolvido por <strong>Cruz.devsoft</strong> | © 2025</small>"
    "</center>",
    unsafe_allow_html=True
)
