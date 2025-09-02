import streamlit as st
from google_planilha import GooglePlanilha
from datetime import datetime


def tela_lente():
    """Tela de reserva de lentes prontas com verificação de estoque."""
    st.subheader("📦 RESERVA DE LENTES PRONTAS")
    st.info(f"**Loja:** {st.session_state.loja}")
    st.info(f"**Usuário:** {st.session_state.nome_atendente}")
    st.markdown("---")

    # --- Conexão com Google Sheets ---
    if 'gsheets' not in st.session_state:
        try:
            st.session_state.gsheets = GooglePlanilha()
        except Exception as e:
            st.error("❌ Falha ao conectar com Google Sheets")
            st.exception(e)
            return
    gsheets = st.session_state.gsheets

    # --- Carregar vendedores ---
    vendedores = _carregar_vendedores(gsheets)
    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
        return

    # --- Formulário de entrada ---
    dados = _formulario_lentes(vendedores)
    if not dados:
        return  # Erro ou dados incompletos

    cliente = dados["cliente"]
    vendedor = dados["vendedor"]
    od = dados["od"]
    oe = dados["oe"]

    # --- Botão: Verificar Estoque ---
    if st.button("🔎 Verificar Estoque", key="btn_verificar_estoque"):
        _verificar_estoque(gsheets, od, oe)

    # --- Botão: Reservar Lentes ---
    if st.button("✅ RESERVAR LENTES", type="primary", use_container_width=True):
        _tentar_reservar(gsheets, od, oe, cliente, vendedor)

    # --- Botão: Voltar ---
    if st.button("↩️ Voltar", use_container_width=True):
        st.session_state.etapa = 'atendimento'
        st.rerun()


# === FUNÇÕES AUXILIARES ===
def _carregar_vendedores(gsheets):
    """Carrega lista de vendedores da loja atual."""
    try:
        vendedores_data = gsheets.get_vendedores_por_loja()
        return [v['VENDEDOR'] for v in vendedores_data] if vendedores_data else []
    except Exception:
        return []


def _formulario_lentes(vendedores):
    """Renderiza campos de entrada e retorna dados validados."""
    cliente = st.text_input("Nome do Paciente", key="cliente_lente_input").strip().upper()
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

    # Validação simples
    if not all([cliente, vendedor, od_esf, od_cil, oe_esf, oe_cil]):
        st.caption("⚠️ Preencha todos os campos para verificar ou reservar.")
        return None

    def formatar(valor):
        return str(valor).replace('.', ',').strip()

    return {
        "cliente": cliente,
        "vendedor": vendedor,
        "od": {"esf": formatar(od_esf), "cil": formatar(od_cil), "qtd": od_qtd},
        "oe": {"esf": formatar(oe_esf), "cil": formatar(oe_cil), "qtd": oe_qtd},
    }


def _verificar_estoque(gsheets, od, oe):
    """Verifica disponibilidade no estoque e exibe resultado."""
    try:
        estoque = gsheets.buscar_estoque_lentes()
        if not estoque:
            st.error("❌ Estoque não carregado. Verifique a aba 'Lentes'.")
            return

        od_disp = estoque.get(od["esf"], {}).get(od["cil"], 0)
        oe_disp = estoque.get(oe["esf"], {}).get(oe["cil"], 0)

        # Exibir status
        cols = st.columns(3)
        cols[0].metric("OD Disponível", od_disp)
        cols[1].metric("OE Disponível", oe_disp)
        cols[2].metric("Status", "✅ OK" if od_disp >= od["qtd"] and oe_disp >= oe["qtd"] else "❌ Falta")

        if od_disp < od["qtd"]:
            st.warning(f"OD: {od['qtd']} solicitados, {od_disp} disponíveis.")
        if oe_disp < oe["qtd"]:
            st.warning(f"OE: {oe['qtd']} solicitados, {oe_disp} disponíveis.")

    except Exception as e:
        st.error("❌ Erro ao verificar estoque:")
        st.exception(e)


def _tentar_reservar(gsheets, od, oe, cliente, vendedor):
    """Tenta realizar a reserva após validar estoque."""
    try:
        # Recarrega estoque atual
        estoque = gsheets.buscar_estoque_lentes()
        if not estoque:
            st.error("❌ Falha ao carregar estoque. Tente novamente.")
            return

        od_disp = estoque.get(od["esf"], {}).get(od["cil"], 0)
        oe_disp = estoque.get(oe["esf"], {}).get(oe["cil"], 0)

        if od_disp < od["qtd"]:
            st.error(f"OD: {od['qtd']} solicitados, {od_disp} disponíveis.")
            return
        if oe_disp < oe["qtd"]:
            st.error(f"OE: {oe['qtd']} solicitados, {oe_disp} disponíveis.")
            return

        # ✅ Faz a reserva
        sucesso = gsheets.reservar_lente_temporariamente(
            od=od,
            oe=oe,
            cliente=cliente,
            vendedor=vendedor
        )

        if sucesso:
            # ✅ Mensagem clara + confirmação visual
            st.success(f"""
            ✅ Reserva confirmada com sucesso!

            - **Paciente:** {cliente}
            - **Lentes:**  
              OD {od['esf']}/{od['cil']} (x{od['qtd']})  
              OE {oe['esf']}/{oe['cil']} (x{oe['qtd']})
            """)
            st.balloons()

            # ✅ Limpa dados temporários da reserva
            chaves_limpar = ['od', 'oe', 'cliente', 'vendedor']
            for key in chaves_limpar:
                if key in st.session_state:
                    del st.session_state[key]

            # ✅ Volta para a tela da LOJA
            st.session_state.etapa = 'loja'
            st.rerun()
        else:
            st.error("❌ Falha ao reservar: estoque insuficiente ou erro interno. Tente novamente.")

    except Exception as e:
        st.error("❌ Erro ao fazer reserva:")
        st.exception(e)

        


# --- ⚠️ REMOVIDO: Bloco __main__ do módulo principal ---
# Para testar localmente, use um arquivo separado: teste_lente.py
