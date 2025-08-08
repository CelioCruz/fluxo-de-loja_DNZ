import streamlit as st
from fpdf import FPDF
import base64
import io
from datetime import datetime
from google_planilha import GooglePlanilha


def tela_encaminhamento():
    st.subheader("🩺 ENCAMINHAMENTO")

    # Inicializa campos no session_state
    if 'enc_cliente' not in st.session_state:
        st.session_state.enc_cliente = ""
    if 'enc_telefone' not in st.session_state:
        st.session_state.enc_telefone = ""
    if 'enc_nascimento' not in st.session_state:
        st.session_state.enc_nascimento = ""
    if 'enc_vendedor' not in st.session_state:
        st.session_state.enc_vendedor = ""
    if 'enc_tipo' not in st.session_state:
        st.session_state.enc_tipo = "PARTICULAR"  # padrão

    # Campo: Nome do Paciente
    cliente_input = st.text_input(
        "Nome do Paciente",
        value=st.session_state.enc_cliente,
        key="enc_cliente_input"
    ).strip().upper()
    if cliente_input != st.session_state.enc_cliente:
        st.session_state.enc_cliente = cliente_input

    # Campo: Telefone
    telefone_input = st.text_input(
        "Telefone",
        value=st.session_state.enc_telefone,
        placeholder="(00) 00000-0000",
        key="enc_telefone_input"
    )
    if st.session_state.enc_telefone != telefone_input:
        st.session_state.enc_telefone = telefone_input

    # Campo: Data de Nascimento
    nascimento_input = st.text_input(
        "Data de Nascimento",
        value=st.session_state.enc_nascimento,
        placeholder="DD/MM/AAAA",
        key="enc_nascimento_input"
    )
    if st.session_state.enc_nascimento != nascimento_input:
        st.session_state.enc_nascimento = nascimento_input

    # Campo: Tipo de Atendimento (PARTICULAR / PLANO)
    tipo_selecionado = st.radio(
        "Tipo de Atendimento",
        options=["PARTICULAR", "PLANO"],
        index=0 if st.session_state.enc_tipo == "PARTICULAR" else 1,
        horizontal=True
    )
    st.session_state.enc_tipo = tipo_selecionado

    # Carrega vendedores
    if 'gsheets' not in st.session_state:
        st.session_state.gsheets = GooglePlanilha()
    gsheets = st.session_state.gsheets
    vendedores_data = gsheets.get_vendedores_por_loja()
    vendedores = [v['VENDEDOR'] for v in vendedores_data] if vendedores_data else []

    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
        return

    # Seleciona vendedor
    st.session_state.enc_vendedor = st.selectbox(
        "Vendedor que encaminhou",
        options=vendedores,
        index=vendedores.index(st.session_state.enc_vendedor)
        if st.session_state.enc_vendedor in vendedores else 0,
        key="sel_vendedor_enc"
    )

    st.markdown("---")

    # Botões: Gerar PDF e Voltar
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🖨️ IMPRIMIR", use_container_width=True):
            try:
                download_link = criar_link_download_pdf()
                st.success("✅ PDF gerado com sucesso!")
                st.markdown(download_link, unsafe_allow_html=True)
                st.session_state.pdf_gerado = True
            except Exception as e:
                st.error(f"❌ Erro ao gerar PDF: {str(e)}")

    with col2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa = 'atendimento'
            st.session_state.subtela = ''
            st.rerun()

    # Botão: Concluído – Voltar à loja
    if st.session_state.get('pdf_gerado', False):
        st.markdown("---")
        if st.button("✅ Concluído – Voltar à loja", use_container_width=True):
            chaves_limpar = [
                'enc_cliente', 'enc_telefone', 'enc_nascimento',
                'enc_vendedor', 'enc_tipo', 'pdf_gerado'
            ]
            for key in chaves_limpar:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.etapa = 'loja'
            st.rerun()


# === GERAÇÃO DE PDF EM MEMÓRIA ===
def gerar_pdf_em_memoria():
    """Gera o PDF com validação e suporte a acentos"""
    try:
        # === Validação dos dados ===
        if not st.session_state.enc_cliente:
            raise ValueError("Nome do paciente é obrigatório")
        if not st.session_state.enc_telefone:
            raise ValueError("Telefone é obrigatório")
        if not st.session_state.enc_nascimento:
            raise ValueError("Data de nascimento é obrigatória")
        if not st.session_state.enc_vendedor:
            raise ValueError("Vendedor é obrigatório")
        if st.session_state.enc_tipo not in ["PARTICULAR", "PLANO"]:
            raise ValueError("Tipo de atendimento inválido")

        # Cria buffer em memória
        pdf_buffer = io.BytesIO()

        # Configura o FPDF
        pdf = FPDF(format='A4', unit='mm')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Tenta usar fonte com suporte a acentos
        # O FPDF padrão não suporta UTF-8 direto, mas se os dados estiverem em string, funciona com Arial
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "ENCAMINHAMENTO", ln=True, align='C')
        pdf.ln(10)

        def add_item(label, value):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(40, 8, f"{label}:", 0, 0)
            pdf.set_font("Arial", '', 12)
            text = str(value) if value else ""
            # Garante que não tenha caracteres problemáticos (opcional)
            text = text.encode('latin1', 'replace').decode('latin1')  # Trata acentos
            pdf.cell(0, 8, f" {text}", ln=True)
            pdf.set_x(10)

        # Dados do paciente
        add_item("Paciente", st.session_state.enc_cliente)
        add_item("Telefone", formatar_telefone(st.session_state.enc_telefone))
        add_item("Nascimento", formatar_data_nascimento(st.session_state.enc_nascimento))
        add_item("Atendimento", st.session_state.enc_tipo)

        # Assinatura
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 6, "Consultor", ln=True, align='C')
        pdf.cell(0, 6, st.session_state.enc_vendedor, ln=True, align='C')

        # ✅ Gera o PDF diretamente no buffer
        # FPDF permite: output() retorna bytes se não passar argumento
        pdf_data = pdf.output()  # Retorna bytes diretamente
        pdf_buffer.write(pdf_data)
        pdf_buffer.seek(0)

        return pdf_buffer

    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")
        return None  # Retorna None em vez de levantar, para não quebrar