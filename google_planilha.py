import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
from typing import Dict, List
import streamlit as st
import os
from datetime import datetime
from zoneinfo import ZoneInfo

class GooglePlanilha:
    def __init__(self):
        if 'gsheets_client' not in st.session_state:
            self._criar_conexao()
        else:
            self.client = st.session_state.gsheets_client
            self.planilha = st.session_state.planilha_atendimento
            self.aba_vendedores = self.planilha.worksheet("vendedor")
            self.aba_relatorio = self.planilha.worksheet("relatorio")

    def _criar_conexao(self):
        try:
            # 🔹 Modo Render: variáveis de ambiente
            if 'GCP_PROJECT_ID' in os.environ:
                credenciais = {
                    "type": "service_account",
                    "project_id": os.environ["GCP_PROJECT_ID"],
                    "private_key_id": os.environ["GCP_PRIVATE_KEY_ID"],
                    "private_key": os.environ["GCP_PRIVATE_KEY"].replace("\\n", "\n"),
                    "client_email": os.environ["GCP_CLIENT_EMAIL"],
                    "client_id": os.environ["GCP_CLIENT_ID"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fluxo-loja%40fluxo-de-loja.iam.gserviceaccount.com",
                    "client_x509_cert_url": os.environ["GCP_CLIENT_X509_CERT_URL"],
                    "universe_domain": "googleapis.com"
                }
            else:
                credenciais = st.secrets["gcp_service_account"]

            # ✅ Conecta com gspread
            client = gspread.service_account_from_dict(credenciais)

            # Salva cliente no session_state
            st.session_state.gsheets_client = client

            # Abre a planilha específica
            try:
                st.info("📖 Abrindo planilha 'fluxo de loja'...")
                planilha = client.open("fluxo de loja")
                st.session_state.planilha_atendimento = planilha
                self.planilha = planilha
                self.aba_vendedores = planilha.worksheet("vendedor")
                self.aba_relatorio = planilha.worksheet("relatorio")
                st.success("✅ Planilha e abas carregadas com sucesso!")
            except SpreadsheetNotFound:
                st.error("❌ Planilha 'fluxo de loja' não encontrada. Verifique o nome exato.")
                st.markdown("💡 Dica: Compartilhe a planilha com `fluxo-loja@fluxo-de-loja.iam.gserviceaccount.com` como **Editor**.")
                st.stop()
            except WorksheetNotFound as e:
                st.error(f"❌ Aba não encontrada: {e}")
                st.stop()

            self._verificar_estrutura()

        except APIError as e:
            # ✅ Captura erros de autenticação, token inválido, etc.
            st.error(f"🔐 Erro de autenticação ou acesso ao Google Sheets.\n\nDetalhes: {str(e)}")
            st.stop()

        except Exception as e:
            st.error(f"❌ Falha inesperada ao conectar ao Google Sheets:\n\n`{str(e)}`")
            st.exception(e)  # Mostra traceback no Streamlit
            st.stop()

    def _verificar_estrutura(self):
        try:
            cabecalhos = self.aba_relatorio.row_values(1)
            esperados = [
                'LOJA', 'VENDEDOR', 'CLIENTE', 'DATA',
                'ATENDIMENTO', 'RECEITA', 'VENDA', 'PERDA', 'RESERVA',
                'PESQUISA', 'CONSULTA', 'HORA'
            ]
            if len(cabecalhos) < 12 or cabecalhos[:12] != esperados:
                st.warning("⚠️ Estrutura da planilha não corresponde ao esperado.")
        except Exception as e:
            st.error(f"❌ Erro ao verificar estrutura: {str(e)}")

    def get_vendedores_por_loja(self, loja: str = None) -> List[Dict]:
        try:
            if 'vendedores_cache' not in st.session_state:
                coluna_a = self.aba_vendedores.col_values(1)
                vendedores = [{"VENDEDOR": nome.strip()} for nome in coluna_a if nome.strip()]
                st.session_state.vendedores_cache = vendedores
            return st.session_state.vendedores_cache
        except Exception as e:
            st.error(f"❌ Falha ao buscar vendedores: {str(e)}")
            return []

    def registrar_atendimento(self, dados: Dict) -> bool:
        try:
            # ✅ Garante que a hora seja sempre do Brasil (Brasília)
            if 'hora' not in dados or not dados['hora']:
                dados['hora'] = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%H:%M:%S")

            # Campos obrigatórios
            if not dados.get('loja'):
                st.error("❌ Loja não definida.")
                return False
            if not dados.get('vendedor'):
                st.error("❌ Vendedor não selecionado.")
                return False
            if not dados.get('cliente'):
                st.error("❌ Nome do cliente é obrigatório.")
                return False

            # Mapeamento de campos para colunas no Google Sheets
            mapeamento = [
                ('loja', 'LOJA'),
                ('vendedor', 'VENDEDOR'),
                ('cliente', 'CLIENTE'),
                ('data', 'DATA'),
                ('atendimento', 'ATENDIMENTO'),
                ('receita', 'RECEITA'),
                ('venda', 'VENDA'),
                ('perda', 'PERDA'),
                ('reserva', 'RESERVA'),
                ('pesquisa', 'PESQUISA'),
                ('consulta', 'CONSULTA'),
                ('hora', 'HORA')
            ]

            # Gera os valores na ordem correta
            valores = [str(dados.get(campo, '')).strip() for campo, _ in mapeamento]

            # Salva na planilha
            self.aba_relatorio.append_row(valores, value_input_option='USER_ENTERED')
            return True

        except Exception as e:
            st.error(f"❌ Falha ao salvar no Google Sheets: {str(e)}")
            return False