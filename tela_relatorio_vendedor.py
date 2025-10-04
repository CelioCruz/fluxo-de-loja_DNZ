# tela_relatorio_vendedor.py

import streamlit as st
import pandas as pd
import sys
import os
import io

# Adiciona o diretório raiz ao sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from google_planilha import GooglePlanilha
except Exception as e:
    st.error(f"Erro ao importar GooglePlanilha: {e}")
    GooglePlanilha = None

def mostrar():
    st.subheader("👨‍💼 RELATÓRIO POR VENDEDOR")
    st.info(f"**Loja:** {st.session_state.get('loja', 'Não definida')}")
    st.info(f"**Usuário:** {st.session_state.get('nome_atendente', 'Desconhecido')}")
    st.markdown("---")

    if GooglePlanilha is None:
        st.warning("⚠️ Módulo GooglePlanilha não carregado.")
        # Botão Voltar aparece mesmo aqui
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_1"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    # Verifica se a loja foi selecionada
    if 'loja' not in st.session_state or not st.session_state.loja:
        st.error("❌ Nenhuma loja selecionada. Volte e escolha uma loja primeiro.")
        st.markdown("---")
        if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_2"):
            st.session_state.etapa = 'loja'
            st.rerun()
        return

    loja_selecionada = st.session_state.loja

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

    # Mesmo sem vendedor selecionado, mostramos o botão no final
    if not vendedor:
        st.info("🔍 Selecione um vendedor para visualizar os registros.")

    else:
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
        else:
            # Identifica colunas
            col_loja = None
            col_vend = None
            for k in todos_registros[0].keys():
                k_low = k.strip().lower()
                if k_low in ['loja', 'unidade', 'filial']:
                    col_loja = k
                if k_low in ['vendedor', 'vendedora', 'funcionário', 'vend']:
                    col_vend = k

            if not col_loja or not col_vend:
                st.error("❌ Colunas 'Loja' ou 'Vendedor' não encontradas.")
            else:
                # Filtra
                dados_filtrados = [
                    r for r in todos_registros
                    if str(r.get(col_loja, "")).strip().lower() == str(loja_selecionada).strip().lower()
                    and str(r.get(col_vend, "")).strip().lower() == str(vendedor).strip().lower()
                ]

                if not dados_filtrados:
                    st.info(f"📭 Nenhum registro encontrado para **{vendedor}** na loja **{loja_selecionada}**.")
                else:
                    # === Processa e exibe os dados ===
                    df = pd.DataFrame(dados_filtrados)

                    colunas_desejadas = {
                        "DATA": ["data", "dt"],
                        "LOJA": ["loja", "unidade", "filial"],
                        "CLIENTE": ["cliente", "nome"],
                        "ATENDIMENTO": ["atendimento", "atend"],
                        "RECEITA": ["receita", "faturamento"],
                        "VENDA": ["venda", "pedidos"],
                        "PERDA": ["perda", "cancelamentos"],
                        "PESQUISA": ["pesquisa", "pesquisas"],
                        "CONSULTA": ["consulta", "exame", "exame de vista"],
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

                    ordem = ["DATA", "LOJA", "CLIENTE", "ATENDIMENTO", "RECEITA", "VENDA", "PERDA", "PESQUISA", "CONSULTA", "RESERVA"]
                    colunas_existentes = [c for c in ordem if c in df.columns]
                    df = df[colunas_existentes].copy()

                    # Limpeza numérica
                    colunas_numericas = ["ATENDIMENTO", "RECEITA", "VENDA", "PERDA", "PESQUISA", "CONSULTA", "RESERVA"]
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
                    st.markdown("### Dados do Vendedor")
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Resumo
                    st.markdown("### Resumo")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Atendimentos", len(df))
                    col2.metric("Receitas", f"{int(df['RECEITA'].sum())}" if "RECEITA" in df.columns and df["RECEITA"].sum() != 0 else "0")
                    col3.metric("Vendas", f"{int(df['VENDA'].sum())}" if "VENDA" in df.columns and df["VENDA"].sum() != 0 else "0")
                    col4.metric("Perdas", f"{int(df['PERDA'].sum())}" if "PERDA" in df.columns and df["PERDA"].sum() != 0 else "0")

                    # Download
                    try:
                        buffer = io.BytesIO()
                        df.to_excel(buffer, index=False, engine="openpyxl")
                        st.download_button(
                            label="📥 Baixar como Excel",
                            data=buffer.getvalue(),
                            file_name=f"Relatorio_{vendedor.replace(' ', '_')}_{loja_selecionada}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except ImportError:
                        st.info("📦 Instale `openpyxl`: `pip install openpyxl`")
                    except Exception as e:
                        st.error(f"Erro ao gerar o arquivo Excel: {e}")

    # ✅ BOTÃO VOLTAR SEMPRE NO FINAL, INDEPENDENTE DO FLUXO
    st.markdown("---")
    if st.button("↩️ Voltar ao Menu", use_container_width=True, key="btn_voltar_menu_relatorio_final"):
        st.session_state.etapa = 'loja'
        st.rerun()