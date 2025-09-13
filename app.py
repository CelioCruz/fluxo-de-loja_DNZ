import streamlit as st
import sys
import os
import base64
import json
import bcrypt
from datetime import datetime
import importlib
import logging

# 🔥 FORÇA O PYTHON A ENCONTRAR OS MÓDULOS NA PASTA DO APP.PY — MESMO NO STREAMLIT GUI
# Isso resolve 99% dos problemas de "ModuleNotFoundError" no Streamlit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ✅✅✅ INICIALIZAÇÃO DE ESTADO — PRIMEIRA COISA NO SCRIPT!
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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Loja", layout="centered")

# --- CONFIGURAÇÃO DE LOG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# 🔹 Função global: atualiza reservas expiradas (com controle de execução)
def atualizar_reservas():
    """Executa limpeza de reservas antigas. Deve ser chamada após ter gsheets."""
    agora = datetime.now()
    ultima_execucao = st.session_state.get("ultima_limpeza_reservas", None)
    
    # Evita executar mais de uma vez por minuto
    if ultima_execucao and (agora - ultima_execucao).total_seconds() < 60:
        return

    try:
        if 'gsheets' in st.session_state:
            count = st.session_state.gsheets.limpar_reservas_antigas(minutos=72*60)  # 72 horas
            if count > 0:
                st.toast(f"✅ {count} reserva(s) expirada(s) removida(s).", icon="🧹")
        st.session_state.ultima_limpeza_reservas = agora
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
    st.error("❌ Falha ao carregar selecionar_loja.py")
    st.exception(e)
    st.stop()

try:
    from tela_atendimento import tela_atendimento_principal
except Exception as e:
    st.error("❌ Falha ao carregar tela_atendimento.py")
    st.exception(e)
    st.stop()

# === FUNÇÃO: Carrega subtela dinamicamente (só quando necessário) ===
def carregar_subtela(nome_subtela):
    """Carrega e retorna a função da subtela solicitada. Executa apenas quando necessário."""
    nome_modulo = f"tela_{nome_subtela}"
    
    # --- DEBUG: Mostra o ambiente atual (para diagnóstico) ---
    st.write("### 🐍 Debug de Importação (apenas para desenvolvimento)")
    st.write(f"🔍 Tentando importar módulo: `{nome_modulo}`")
    st.write(f"📂 Diretório atual: `{os.getcwd()}`")
    st.write(f"📋 Caminhos do Python (sys.path):")
    for i, p in enumerate(sys.path):
        st.write(f"   {i}: {p}")

    # --- FORÇA ADICIONAR O DIRETÓRIO DO PROJETO (garantia extra) ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        st.info(f"✅ Adicionado ao sys.path: `{current_dir}`")

    try:
        # 🔥 FORÇA RECARGA DO MÓDULO SE JÁ ESTIVER CARREGADO (evita cache antigo)
        if nome_modulo in sys.modules:
            logger.info(f"🔁 Recarregando módulo: {nome_modulo}")
            importlib.reload(sys.modules[nome_modulo])

        module = importlib.import_module(nome_modulo)
        logger.info(f"✅ Módulo '{nome_modulo}' carregado com sucesso!")

        # Lista funções disponíveis para debug
        funcoes_disponiveis = [name for name in dir(module) if not name.startswith('_') and callable(getattr(module, name))]
        logger.info(f"📌 Funções disponíveis em {nome_modulo}: {funcoes_disponiveis}")

        # ✅ Prioridade 1: Função 'mostrar()' (padrão recomendado)
        if hasattr(module, 'mostrar'):
            logger.info(f"🎯 Encontrada função: 'mostrar()' → Usando como padrão")
            return module.mostrar

        # ✅ Prioridade 2: Função com mesmo nome do módulo (ex: tela_exame_vista)
        elif hasattr(module, nome_modulo):
            logger.info(f"🎯 Encontrada função: '{nome_modulo}()' → Usando função principal")
            return getattr(module, nome_modulo)

        # ✅ Prioridade 3: Função sem prefixo 'tela_' (ex: exame_vista)
        elif hasattr(module, nome_subtela):
            logger.info(f"🎯 Encontrada função: '{nome_subtela}()' → Fallback")
            return getattr(module, nome_subtela)

        else:
            logger.warning(f"⚠️ Nenhuma função válida encontrada em {nome_modulo}. Esperava: 'mostrar()', '{nome_modulo}()', ou '{nome_subtela}()'")
            st.error(f"❌ Falha ao carregar `{nome_modulo}.py`: nenhuma função válida encontrada.")
            st.write(f"💡 Funções disponíveis: {', '.join(funcoes_disponiveis)}")
            def erro():
                st.error(f"❌ Nenhuma função válida encontrada no módulo `{nome_modulo}`")
            return erro

    except ModuleNotFoundError:
        st.error(f"❌ Módulo não encontrado: `{nome_modulo}`")
        st.error("❗ Isso é estranho — o arquivo existe na pasta, mas o Streamlit não consegue encontrar.")
        st.error("💡 Soluções possíveis:")
        st.error("   1. Reinicie o servidor Streamlit (Ctrl+C → novo terminal → rerun)")
        st.error("   2. Verifique se o arquivo `tela_exame_vista.py` está na mesma pasta que app.py")
        st.error("   3. Confirme que o ambiente Python do Streamlit é o mesmo onde os arquivos estão instalados")
        st.error("   4. Execute: `streamlit cache clear` e reinicie")
        def erro():
            st.error(f"❌ Não foi possível carregar `{nome_modulo}`")
        return erro

    except Exception as e:
        logger.error(f"❌ Falha ao carregar {nome_modulo}: {e}")
        st.error(f"❌ Erro inesperado ao carregar `{nome_modulo}`: {str(e)}")
        def erro():
            st.error(f"❌ Erro interno: {str(e)}")
        return erro

# === FUNÇÃO: Garantir conexão com Google Sheets ===
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

# === NAVEGAÇÃO ENTRE TELAS ===
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

    nome_subtela = st.session_state.subtela
    func_subtela = carregar_subtela(nome_subtela)  # ⬅️ Carrega DINAMICAMENTE aqui
    if func_subtela:
        func_subtela()  # Executa a função da subtela
    else:
        st.error("❌ Tela não encontrada.")
        if st.button("Voltar ao início", key="btn_voltar_inicio"):
            st.session_state.etapa = 'login'
            st.rerun()

else:
    st.error("⚠️ Etapa inválida.")
    st.session_state.etapa = 'login'
    st.rerun()

# --- SIDEBAR: Informações do usuário e logout ---
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

# --- RODAPÉ ---
st.markdown(
    "<br><hr><center>"
    "<small>💼 Projeto <strong>Leonardo Pesil</strong>, desenvolvido por <strong>Cruz.devsoft</strong> | © 2025</small>"
    "</center>",
    unsafe_allow_html=True
)