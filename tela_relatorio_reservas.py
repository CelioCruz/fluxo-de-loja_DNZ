import streamlit as st
import pandas as pd
from datetime import datetime

def mostrar():
    st.subheader("📋 RELATÓRIO DE RESERVAS ATIVAS")
    
    if 'gsheets' not in st.session_state:
        from google_planilha import GooglePlanilha
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets

    try:
        with st.spinner("Carregando dados..."):
            todos_registros = gsheets.aba_relatorio.get_all_records()
    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {e}")
        if st.button("↩️ Voltar"):
            st.session_state.etapa = 'atendimento'
            st.rerun()
        return

    if not todos_registros:
        st.info("📭 Nenhum dado encontrado.")
        if st.button("↩️ Voltar"):
            st.session_state.etapa = 'atendimento'
            st.rerun()
        return

    df_total = pd.DataFrame(todos_registros)
    
    # Identificar colunas
    cols_map = {c.strip().upper(): c for c in df_total.columns}
    col_reserva = cols_map.get('RESERVAS')
    col_vendedor = cols_map.get('VENDEDOR')
    col_cliente = cols_map.get('CLIENTE')
    col_loja = cols_map.get('LOJA')
    col_data = cols_map.get('DATA')

    if not all([col_reserva, col_vendedor, col_cliente, col_loja, col_data]):
        st.error("❌ Estrutura da planilha inválida. Verifique as colunas.")
        if st.button("↩️ Voltar"):
            st.session_state.etapa = 'atendimento'
            st.rerun()
        return

    # Limpeza e conversão da coluna RESERVAS
    df_total[col_reserva] = pd.to_numeric(df_total[col_reserva], errors='coerce').fillna(0).astype(int)
    
    # Filtrar pela loja selecionada (logada)
    loja_atual = str(st.session_state.get('loja', '')).strip().upper()
    if loja_atual:
        df_total = df_total[df_total[col_loja].astype(str).str.strip().str.upper() == loja_atual]

    # Filtrar apenas o que tem relação com reserva (1 ou -1)
    df_reservas = df_total[df_total[col_reserva] != 0].copy()

    # Agrupar para encontrar reservas ativas por Loja, Vendedor e Cliente
    df_agrupado = df_reservas.groupby([col_vendedor, col_cliente]).agg({
        col_reserva: 'sum',
        col_data: 'max'
    }).reset_index()

    # Reservas ativas (saldo > 0)
    df_ativas = df_agrupado[df_agrupado[col_reserva] > 0].copy()

    if df_ativas.empty:
        st.info(f"✅ Não há reservas ativas para a loja {loja_atual}.")
        if st.button("↩️ VOLTAR"):
            st.session_state.etapa = 'atendimento'
            st.rerun()
        return

    # --- FILTRO SUPERIOR ---
    vendedores = sorted(df_ativas[col_vendedor].unique().tolist())
    vendedor_sel = st.selectbox("👤 Vendedor - (Filtrar por Vendedor)", ["TODOS"] + vendedores)

    if vendedor_sel != "TODOS":
        df_exibir = df_ativas[df_ativas[col_vendedor] == vendedor_sel].copy()
    else:
        df_exibir = df_ativas.copy()

    # Renomear colunas para o padrão solicitado
    df_exibir = df_exibir.rename(columns={
        col_data: "DATA",
        col_cliente: "CLIENTE",
        col_reserva: "QUANTIDADE",
        col_vendedor: "VENDEDOR"
    })

    # Reordenar colunas
    colunas_finais = ["DATA", "CLIENTE", "QUANTIDADE"]
    if vendedor_sel == "TODOS":
        colunas_finais.append("VENDEDOR")

    st.markdown("---")
    st.markdown(f"### 📋 Lista de Reservas Ativas")
    st.dataframe(df_exibir[colunas_finais], use_container_width=True, hide_index=True)

    # Exibe um totalizador rápido
    total_reservas = df_exibir["QUANTIDADE"].sum()
    st.info(f"**Total de Reservas Ativas no filtro:** {total_reservas}")

    st.markdown("---")
    if st.button("↩️ VOLTAR AO MENU", use_container_width=True):
        st.session_state.etapa = 'atendimento'
        st.rerun()
