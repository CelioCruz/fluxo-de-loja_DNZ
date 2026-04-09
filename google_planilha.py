import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
from typing import Dict, List
import streamlit as st
import os
import json
import re
from dateutil import parser
import pytz
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from io import StringIO
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


class GooglePlanilha:
    """
    Classe para integração com Google Sheets e Drive.
    """

    COLUNAS_RELATORIO = [
        'LOJA', 'DATA', 'HORA', 'VENDEDOR', 'CLIENTE', 'ATENDIMENTOS', 'RECEITAS',
        'PERDAS', 'VENDAS', 'RESERVAS', 'PESQUISAS', 'EXAME DE VISTA', 'GOOGLE'
    ]

    def __init__(self):
        if 'gsheets_client' not in st.session_state:
            self._criar_conexao()
        else:
            self.client = st.session_state.gsheets_client
            self.planilha = st.session_state.planilha_atendimento
            self.aba_vendedores = self._get_worksheet("vendedor")
            self.aba_relatorio = self._get_worksheet("relatorio")

    def _criar_conexao(self):
        try:
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
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.environ["GCP_CLIENT_X509_CERT_URL"],
                    "universe_domain": "googleapis.com"
                }
            else:
                credenciais = st.secrets["gcp_service_account"]

            client = gspread.service_account_from_dict(credenciais)
            st.session_state.gsheets_client = client
            planilha = client.open("fluxo de loja")
            st.session_state.planilha_atendimento = planilha
            self.planilha = planilha
            self.aba_vendedores = self._get_worksheet("vendedor")
            self.aba_relatorio = self._get_worksheet("relatorio")
            self._verificar_estrutura()
        except Exception as e:
            st.error(f"❌ Falha ao conectar: {e}")

    def _get_worksheet(self, name: str):
        try: return self.planilha.worksheet(name)
        except: return None

    def _verificar_estrutura(self):
        if not self.aba_relatorio: return
        try:
            cabecalhos = [c.strip() for c in self.aba_relatorio.row_values(1)]
            # Ajuste para renomear se for GOOGLE1
            if "GOOGLE1" in cabecalhos:
                idx = cabecalhos.index("GOOGLE1")
                self.aba_relatorio.update_cell(1, idx + 1, "GOOGLE")
                cabecalhos[idx] = "GOOGLE"
            
            if len(cabecalhos) < len(self.COLUNAS_RELATORIO) or cabecalhos[:len(self.COLUNAS_RELATORIO)] != self.COLUNAS_RELATORIO:
                self.aba_relatorio.update("A1", [self.COLUNAS_RELATORIO])
        except: pass

    def registrar_atendimento(self, dados: Dict) -> bool:
        """Registra novo atendimento na planilha."""
        try:
            for campo in ['loja', 'vendedor', 'cliente']:
                if not dados.get(campo):
                    st.error(f"❌ {campo.upper()} é obrigatório.")
                    return False

            fuso = ZoneInfo("America/Sao_Paulo")
            agora = datetime.now(fuso)
            dados['hora'] = dados.get('hora') or agora.strftime("%H:%M:%S")
            dados['data'] = dados.get('data') or agora.strftime("%d/%m/%Y")

            mapeamento = [
                ('loja', 'LOJA'), ('data', 'DATA'), ('hora', 'HORA'),
                ('vendedor', 'VENDEDOR'), ('cliente', 'CLIENTE'),
                ('atendimento', 'ATENDIMENTOS'), ('receita', 'RECEITAS'),
                ('perda', 'PERDAS'), ('venda', 'VENDAS'), ('reserva', 'RESERVAS'),
                ('pesquisa', 'PESQUISAS'), ('consulta', 'EXAME DE VISTA'),
                ('google', 'GOOGLE') # Mapeamento da coluna M renomeado
            ]
            
            valores = [str(dados.get(campo, '')).strip() for campo, _ in mapeamento]
            self.aba_relatorio.append_row(valores, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            st.error(f"❌ Falha ao salvar: {e}")
            return False

    def get_vendedores_por_loja(self, loja: str = None) -> List[Dict]:
        try:
            # Não usa mais cache para permitir ver mudanças de status
            dados = self.aba_vendedores.get_all_values() if self.aba_vendedores else []
            if not dados: return []
            
            vendedores = []
            for i, linha in enumerate(dados):
                if not linha: continue
                nome = linha[0].strip()
                if not nome or nome.upper() == "VENDEDOR": continue
                
                status = "ATIVO"
                if len(linha) > 1:
                    status = linha[1].strip().upper() or "ATIVO"
                
                vendedores.append({"VENDEDOR": nome, "STATUS": status, "row": i + 1})
            
            # Por padrão, as telas de atendimento só vêem ATIVOS
            return [v for v in vendedores if v["STATUS"] == "ATIVO"]
        except: return []

    def get_todos_vendedores(self) -> List[Dict]:
        try:
            dados = self.aba_vendedores.get_all_values() if self.aba_vendedores else []
            if not dados: return []
            
            vendedores = []
            for i, linha in enumerate(dados):
                if not linha: continue
                nome = linha[0].strip()
                if not nome or nome.upper() == "VENDEDOR": continue
                
                status = "ATIVO"
                if len(linha) > 1:
                    status = linha[1].strip().upper() or "ATIVO"
                
                vendedores.append({"VENDEDOR": nome, "STATUS": status, "row": i + 1})
            return vendedores
        except: return []

    def adicionar_vendedor(self, nome: str) -> bool:
        try:
            if not self.aba_vendedores: return False
            self.aba_vendedores.append_row([nome.upper(), "ATIVO"])
            if 'vendedores_cache' in st.session_state: del st.session_state.vendedores_cache
            return True
        except: return False

    def atualizar_status_vendedor(self, row: int, novo_status: str) -> bool:
        try:
            if not self.aba_vendedores: return False
            self.aba_vendedores.update_cell(row, 2, novo_status.upper())
            if 'vendedores_cache' in st.session_state: del st.session_state.vendedores_cache
            return True
        except: return False

    def limpar_reservas_antigas(self, minutos=1) -> int:
        aba_reservas = self._get_worksheet("reservas")
        if not aba_reservas: return 0
        try:
            dados = aba_reservas.get_all_values()
            if len(dados) < 2: return 0
            agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
            count = 0
            for i in range(len(dados)-1, 0, -1):
                linha = dados[i]
                if len(linha) > 5 and linha[5].strip().upper() == "PENDENTE":
                    try:
                        criacao = parser.parse(linha[0], dayfirst=True).replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
                        if (agora - criacao).total_seconds() > minutos * 60:
                            aba_reservas.delete_rows(i + 1)
                            count += 1
                    except: continue
            return count
        except: return 0
