import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, List
import streamlit as st

class GooglePlanilha:
    def __init__(self):
        """Inicializa ou reutiliza a conexão com o Google Sheets"""
        if 'gsheets_client' not in st.session_state:
            self._criar_conexao()
        else:
            self.client = st.session_state.gsheets_client
            self.planilha = st.session_state.planilha_atendimento
            self.aba_vendedores = self.planilha.worksheet("vendedor")
            self.aba_relatorio = self.planilha.worksheet("relatorio")

    def _criar_conexao(self):
        """Cria a conexão com o Google Sheets usando a nova conta de serviço"""
        try:
            # ✅ Carrega as credenciais do secrets.toml
            credenciais = st.secrets["gcp_service_account"]

            # ✅ Usa gspread moderno (não use ServiceAccountCredentials)
            import gspread
            from google.auth.exceptions import DefaultCredentialsError

            # Cria cliente diretamente a partir do dicionário
            client = gspread.service_account_from_dict(credenciais)

            # Armazena na sessão
            st.session_state.gsheets_client = client
            st.session_state.planilha_atendimento = client.open("fluxo de loja")

            self.client = client
            self.planilha = st.session_state.planilha_atendimento
            self.aba_vendedores = self.planilha.worksheet("vendedor")
            self.aba_relatorio = self.planilha.worksheet("relatorio")

            # Verifica se a estrutura da planilha está correta
            self._verificar_estrutura()

        except Exception as e:
            st.error(f"❌ Falha ao conectar ao Google Sheets:\n{str(e)}")
            st.stop()

    def _verificar_estrutura(self):
        """Verifica se a aba 'relatorio' tem os cabeçalhos esperados"""
        try:
            cabecalhos = self.aba_relatorio.row_values(1)
            colunas_esperadas = [
                'LOJA', 'VENDEDOR', 'CLIENTE', 'DATA',
                'ATENDIMENTO', 'RECEITA', 'VENDA', 'PERDA', 'RESERVA',
                'PESQUISA', 'CONSULTA', 'HORA'
            ]

            if len(cabecalhos) < 12 or cabecalhos[:12] != colunas_esperadas: # type: ignore
                st.warning(
                    "⚠️ A estrutura da planilha 'relatorio' não corresponde ao esperado.\n"
                    "Verifique se as colunas estão na ordem correta de A até L."
                )
        except Exception as e:
            st.error(f"❌ Erro ao verificar estrutura: {str(e)}")

    def get_vendedores_por_loja(self, loja: str = None) -> List[Dict]:
        """Retorna lista de vendedores, com cache para evitar múltiplas leituras"""
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
        """Registra um novo atendimento usando append_row (mais rápido e seguro)"""
        try:
            # Mapeamento dos campos para as colunas na ordem correta
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

            # Prepara os valores na ordem correta
            valores = [str(dados.get(campo, '')).strip() for campo, _ in mapeamento]

            # ✅ append_row é mais rápido e não precisa calcular linha
            self.aba_relatorio.append_row(valores, value_input_option='USER_ENTERED')
            return True

        except Exception as e:
            st.error(f"❌ Falha ao salvar no Google Sheets:\n{str(e)}")
            return False

    def registrar_sem_vendedor(self, dados: Dict) -> bool:
        """Versão alternativa para registros sem vendedor (ex: garantia, ajuste)"""
        try:
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

            # Campos obrigatórios
            campos_obrigatorios = ['loja', 'data']
            for campo in campos_obrigatorios:
                if not dados.get(campo):
                    st.error(f"⚠️ Campo obrigatório faltando: {campo}")
                    return False

            valores = [str(dados.get(campo, '')).strip() for campo, _ in mapeamento]

            # ✅ append_row (mais rápido)
            self.aba_relatorio.append_row(valores, value_input_option='USER_ENTERED')
            return True

        except Exception as e:
            st.error(f"❌ Falha ao salvar (sem vendedor): {str(e)}")
            return False