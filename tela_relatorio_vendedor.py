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

    # === Usa ou inicializa GooglePlanilha ===
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

    # === Carrega vendedores da loja ===
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

    # === Seleção de vendedor ===
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

    # === Busca registros do vendedor na loja ===
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

    # Identifica colunas
    col_loja = col_vend = col_data = None
    for k in todos_registros[0].keys():
        k_low = k.strip().lower()
        if k_low in ['loja', 'unidade', 'filial']:
            col_loja = k
        if k_low in ['vendedor', 'vendedora', 'funcionário', 'vend']:
            col_vend = k
        if k_low in ['data', 'datas', 'dt']:
            col_data = k

    if not col_loja or not col_vend or not col_data:
        st.error("❌ Colunas 'Loja', 'Vendedor' ou 'Data' não encontradas.")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_sem_colunas"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    # Filtra: loja + vendedor + data = hoje
    dados_filtrados = []
    for r in todos_registros:
        # Verifica loja e vendedor
        if str(r.get(col_loja, "")).strip().lower() != str(loja_selecionada).strip().lower():
            continue
        if str(r.get(col_vend, "")).strip().lower() != str(vendedor).strip().lower():
            continue
        # Verifica data
        data_row = parse_date(r.get(col_data, ""))
        if data_row == hoje:
            dados_filtrados.append(r)

    if not dados_filtrados:
        st.info(f"📭 Nenhum registro encontrado para **{vendedor}** na loja **{loja_selecionada}** em **{hoje.strftime('%d/%m/%Y')}**.")
    else:
        # === Processa e exibe os dados (mesma lógica) ===
        df = pd.DataFrame(dados_filtrados)

        colunas_desejadas = {
            "DATA": ["data", "dt"],
            "LOJA": ["loja", "unidade", "filial"],
            "CLIENTE": ["cliente", "nome"],
            "RECEITA": ["receita", "faturamento"],
            "VENDA": ["venda", "pedidos"],
            "PERDA": ["perda", "cancelamentos"],
            "RESERVA": ["reserva", "agendamento"]
        }

        colunas_finais = {}
        for nome, palavras in colunas_desejadas.items():
            for col in df.columns:
                if any(p in col.lower() for p in palavras):
                    colunas_finais[col] = nome
                    break

        if colunas_finais:
            df = df[list(colunas_finais.keys())].rename(columns=colunas_finais)

        ordem = ["DATA", "LOJA", "CLIENTE", "RECEITA", "VENDA", "PERDA", "RESERVA"]
        colunas_existentes = [c for c in ordem if c in df.columns]
        df = df[colunas_existentes].copy()

        # Limpeza numérica
        colunas_numericas = ["RECEITA", "VENDA", "PERDA", "RESERVA"]
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = df[col].astype(str)
                df[col] = df[col].str.strip().replace(
                    ["", "nan", "None", "NaN", "null", "–", "-", " ", "R$", "R$ ", "r$", "r$ "],
                    "0"
                )
                df[col] = df[col].str.replace(r"[^\d.,-]", "", regex=True)
                df[col] = df[col].str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        for col in ["ATENDIMENTO", "PESQUISA", "CONSULTA", "PERDA"]:
            if col in df.columns:
                df[col] = df[col].astype(int)

        for col in ["RECEITA", "VENDA", "RESERVA"]:
            if col in df.columns:
                df[col] = df[col].round(2).apply(lambda x: int(x) if x == int(x) else x)

        # Exibe tabela
        st.markdown("### Dados do Vendedor (Hoje)")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Resumo
        st.markdown("### Resumo (Hoje)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Receitas", f"{int(df['RECEITA'].sum())}" if "RECEITA" in df.columns and df["RECEITA"].sum() != 0 else "0")
        col2.metric("Vendas", f"{int(df['VENDA'].sum())}" if "VENDA" in df.columns and df["VENDA"].sum() != 0 else "0")
        col3.metric("Perdas", f"{int(df['PERDA'].sum())}" if "PERDA" in df.columns and df["PERDA"].sum() != 0 else "0")
        col4.metric("Reservas", f"{int(df['RESERVA'].sum())}" if "RESERVA" in df.columns and df["RESERVA"].sum() != 0 else "0")
        # Download
        try:
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            st.download_button(
                label="📥 Baixar como Excel",
                data=buffer.getvalue(),
                file_name=f"Relatorio_Hoje_{vendedor.replace(' ', '_')}_{loja_selecionada}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except ImportError:
            st.info("📦 Instale `openpyxl`: `pip install openpyxl`")
        except Exception as e:
            st.error(f"Erro ao gerar o arquivo Excel: {e}")

    # ✅ BOTÃO VOLTAR SEMPRE NO FINAL
    st.markdown("---")
    if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_final"):
        st.session_state.etapa = 'loja'
        st.rerun()