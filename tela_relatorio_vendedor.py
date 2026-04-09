import streamlit as st
import pandas as pd
import sys
import os
import io
from datetime import datetime

# Adiciona o diretório raiz ao sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from google_planilha import GooglePlanilha
except Exception as e:
    st.error(f"Erro ao importar GooglePlanilha: {e}")
    GooglePlanilha = None

def parse_date(date_str):
    """Converte string no formato dd/mm/yyyy para date ou None."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None

def mostrar():
    st.subheader("👨‍💼 RELATÓRIO POR VENDEDOR — HOJE")
    st.info(f"**Loja:** {st.session_state.get('loja', 'Não definida')}")
    st.info(f"**Usuário:** {st.session_state.get('nome_atendente', 'Desconhecido')}")
    st.markdown("---")

    if GooglePlanilha is None:
        st.warning("⚠️ Módulo GooglePlanilha não carregado.")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_1"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    if 'loja' not in st.session_state or not st.session_state.loja:
        st.error("❌ Nenhuma loja selecionada. Volte e escolha uma loja primeiro.")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_2"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    loja_selecionada = st.session_state.loja
    hoje = datetime.now().date()

    if 'gsheets' not in st.session_state:
        try:
            st.session_state.gsheets = GooglePlanilha()
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao Google Sheets: {e}")
            st.markdown("---")
            if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_3"):
                st.session_state.etapa = 'loja'
                st.rerun()
            return
    gsheets = st.session_state.gsheets

    try:
        vendedores_data = gsheets.get_vendedores_por_loja()
        vendedores = [v['VENDEDOR'] for v in vendedores_data]
    except Exception as e:
        st.error(f"Erro ao carregar vendedores: {e}")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_4"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado para esta loja.")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_5"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    vendedor = st.selectbox(
        "Vendedor",
        vendedores,
        index=None,
        placeholder="Selecione o vendedor",
        key="vend_relatorio"
    )

    if not vendedor:
        st.info("🔍 Selecione um vendedor para visualizar os registros de **hoje**.")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_sem_vend"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    try:
        todos_registros = gsheets.aba_relatorio.get_all_records()
    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {e}")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_6"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    if not todos_registros:
        st.info("📭 Nenhum dado encontrado na planilha de relatórios.")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_sem_dados"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    col_loja = col_vend = col_data = None
    for k in todos_registros[0].keys():
        k_low = k.strip().lower()
        if k_low in ['loja', 'unidade', 'filial']: col_loja = k
        if k_low in ['vendedor', 'vendedora', 'funcionário', 'vend']: col_vend = k
        if k_low in ['data', 'datas', 'dt']: col_data = k

    if not col_loja or not col_vend or not col_data:
        st.error("❌ Colunas básicas não encontradas.")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    dados_filtrados = []
    for r in todos_registros:
        if str(r.get(col_loja, "")).strip().lower() != str(loja_selecionada).strip().lower(): continue
        if str(r.get(col_vend, "")).strip().lower() != str(vendedor).strip().lower(): continue
        if parse_date(r.get(col_data, "")) == hoje: dados_filtrados.append(r)

    if not dados_filtrados:
        st.info(f"📭 Nenhum registro para **{vendedor}** em **{hoje.strftime('%d/%m/%Y')}**.")
    else:
        df = pd.DataFrame(dados_filtrados)

        colunas_desejadas = {
            "DATA": ["data", "dt"],
            "LOJA": ["loja", "unidade", "filial"],
            "CLIENTE": ["cliente", "nome"],
            "RECEITA": ["receita", "faturamento"],
            "VENDA": ["venda", "pedidos"],
            "PERDA": ["perda", "cancelamentos"],
            "RESERVA": ["reserva", "agendamento"],
            "GOOGLE": ["google"] # Adicionado campo Google
        }

        colunas_finais = {}
        for nome, palavras in colunas_desejadas.items():
            for col in df.columns:
                if any(p in col.lower() for p in palavras):
                    colunas_finais[col] = nome
                    break

        if colunas_finais:
            df = df[list(colunas_finais.keys())].rename(columns=colunas_finais)

        # Ordem solicitada: Google após Reserva
        ordem = ["DATA", "LOJA", "CLIENTE", "RECEITA", "VENDA", "PERDA", "RESERVA", "GOOGLE"]
        colunas_existentes = [c for c in ordem if c in df.columns]
        df = df[colunas_existentes].copy()

        # Limpeza numérica incluindo GOOGLE
        colunas_numericas = ["RECEITA", "VENDA", "PERDA", "RESERVA", "GOOGLE"]
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().replace(
                    ["", "nan", "None", "NaN", "null", "–", "-", " ", "R$", "R$ "], "0"
                )
                df[col] = df[col].str.replace(r"[^\d.,-]", "", regex=True).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Exibe tabela
        st.markdown("### Dados do Vendedor (Hoje)")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Resumo com campo Google adicionado
        st.markdown("### Resumo (Hoje)")
        m1, m2, m3, m4, m5 = st.columns(5)
        
        def get_sum(col):
            return int(df[col].sum()) if col in df.columns else 0

        m1.metric("Receitas", f"{get_sum('RECEITA')}")
        m2.metric("Vendas", f"{get_sum('VENDA')}")
        m3.metric("Perdas", f"{get_sum('PERDA')}")
        m4.metric("Reservas", f"{get_sum('RESERVA')}")
        m5.metric("Google", f"{get_sum('GOOGLE')}") # Novo campo no resumo

        # Download
        try:
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            st.download_button(
                label="📥 Baixar como Excel",
                data=buffer.getvalue(),
                file_name=f"Relatorio_{vendedor}_{hoje.strftime('%d%m%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except: pass

    st.markdown("---")
    if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_final"):
        st.session_state.etapa = 'loja'
        st.rerun()
