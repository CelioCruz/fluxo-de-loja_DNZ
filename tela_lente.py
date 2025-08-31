import streamlit as st
from google_planilha import GooglePlanilha
from datetime import datetime

def tela_lente():
    st.subheader("📦 RESERVA DE LENTES PRONTAS")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    # Conecta com Google Sheets
    if 'gsheets' not in st.session_state:
        try:
            st.session_state.gsheets = GooglePlanilha()
        except Exception as e:
            st.error("❌ Falha ao conectar com Google Sheets")
            st.exception(e)
            return
    gsheets = st.session_state.gsheets

    # Carrega vendedores
    try:
        vendedores_data = gsheets.get_vendedores_por_loja()
        vendedores = [v['VENDEDOR'] for v in vendedores_data] if vendedores_data else []
    except Exception:
        vendedores = []

    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
        return

    # Campos principais
    cliente = st.text_input("Nome do Paciente", key="cliente_lente_input").upper()
    vendedor = st.selectbox("Vendedor", vendedores, index=None, placeholder="Selecione", key="vend_lente")

    st.markdown("### 🔍 Receita Oftálmica")

    col_od, col_oe = st.columns(2)

    with col_od:
        st.markdown("**🔹 OD (Olho Direito)**")
        od_esf = st.text_input("Esferico OD", key="od_esf").strip()
        od_cil = st.text_input("Cilíndrico OD", key="od_cil").strip()
        od_qtd = st.number_input("Qtd OD", min_value=1, value=1, step=1, key="od_qtd")

    with col_oe:
        st.markdown("**🔸 OE (Olho Esquerdo)**")
        oe_esf = st.text_input("Esferico OE", key="oe_esf").strip()
        oe_cil = st.text_input("Cilíndrico OE", key="oe_cil").strip()
        oe_qtd = st.number_input("Qtd OE", min_value=1, value=1, step=1, key="oe_qtd")

    # --- BOTÃO: VERIFICAR ESTOQUE ---
    if st.button("🔎 Verificar Estoque", key="btn_verificar_estoque"):
        if not all([cliente, vendedor, od_esf, od_cil, oe_esf, oe_cil]):
            st.error("⚠️ Preencha todos os campos!")
        else:
            try:
                # Padroniza entrada
                def fmt(v):
                    return str(v).replace('.', ',').strip()

                od_esf_f = fmt(od_esf)
                od_cil_f = fmt(od_cil)
                oe_esf_f = fmt(oe_esf)
                oe_cil_f = fmt(oe_cil)

                # Busca estoque
                estoque = gsheets.buscar_estoque_lentes()
                if not estoque:
                    st.error("❌ Estoque não carregado. Verifique a aba 'Lentes'.")
                    return

                od_disp = estoque.get(od_esf_f, {}).get(od_cil_f, 0)
                oe_disp = estoque.get(oe_esf_f, {}).get(oe_cil_f, 0)

                # Mostra resultado
                cols = st.columns(3)
                cols[0].metric("OD Disponível", od_disp)
                cols[1].metric("OE Disponível", oe_disp)
                cols[2].metric(
                    "Status",
                    "✅ OK" if od_disp >= od_qtd and oe_disp >= oe_qtd else "❌ Falta"
                )

                if od_disp < od_qtd:
                    st.warning(f"OD: {od_qtd} solicitados, {od_disp} disponíveis.")
                if oe_disp < oe_qtd:
                    st.warning(f"OE: {oe_qtd} solicitados, {oe_disp} disponíveis.")

                # Salva para reserva
                st.session_state.od = {"esf": od_esf_f, "cil": od_cil_f, "qtd": od_qtd}
                st.session_state.oe = {"esf": oe_esf_f, "cil": oe_cil_f, "qtd": oe_qtd}
                st.session_state.cliente = cliente
                st.session_state.vendedor = vendedor

            except Exception as e:
                st.error("❌ Erro ao verificar estoque:")
                st.exception(e)
                
    # --- BOTÃO: RESERVAR LENTES (único botão) ---
    if st.button("✅ RESERVAR LENTES", type="primary", use_container_width=True):
        if not all([cliente, vendedor, od_esf, od_cil, oe_esf, oe_cil]):
            st.error("⚠️ Preencha todos os campos!")
        else:
            try:
                # ✅ Garante que a conexão com Google Sheets está ativa
                if 'gsheets' not in st.session_state:
                    st.error("❌ Sistema não conectado ao Google Sheets. Recarregue a página.")
                    st.stop()

                gsheets = st.session_state.gsheets

                # ✅ Verifica estoque atual
                estoque = gsheets.buscar_estoque_lentes()
                if not estoque:
                    st.error("❌ Falha ao carregar estoque. Verifique a aba 'Lentes'.")
                    st.stop()

                # Padroniza valores
                def fmt(v):
                    return str(v).replace('.', ',').strip()

                od_esf_f = fmt(od_esf)
                od_cil_f = fmt(od_cil)
                oe_esf_f = fmt(oe_esf)
                oe_cil_f = fmt(oe_cil)

                od_disp = estoque.get(od_esf_f, {}).get(od_cil_f, 0)
                oe_disp = estoque.get(oe_esf_f, {}).get(oe_cil_f, 0)

                if od_disp < od_qtd:
                    st.error(f"OD: {od_qtd} solicitados, {od_disp} disponíveis.")
                    return
                if oe_disp < oe_qtd:
                    st.error(f"OE: {oe_qtd} solicitados, {oe_disp} disponíveis.")
                    return

                # ✅ Faz a reserva
                sucesso = gsheets.reservar_lente_temporariamente(
                    od={"esf": od_esf_f, "cil": od_cil_f, "qtd": od_qtd},
                    oe={"esf": oe_esf_f, "cil": oe_cil_f, "qtd": oe_qtd},
                    cliente=cliente,
                    vendedor=vendedor
                )

                if sucesso:
                    st.success("✅ Reserva registrada! Aguarde a baixa do sistema.")
                    st.balloons()
                    st.session_state.etapa = 'loja'
                    st.rerun()
                else:
                    st.error("❌ Falha ao reservar: estoque insuficiente ou erro interno. Tente novamente.")

            except Exception as e:
                st.error("❌ Erro ao fazer reserva:")
                st.exception(e)
    

    # --- BOTÃO: VOLTAR ---
    if st.button("↩️ Voltar", use_container_width=True):
        st.session_state.etapa = 'atendimento'
        st.rerun()

# Para testar localmente
if __name__ == "__main__":
    if 'loja' not in st.session_state:
        st.session_state.loja = "Loja Teste"
    if 'nome_atendente' not in st.session_state:
        st.session_state.nome_atendente = "TESTE"
    tela_lente()