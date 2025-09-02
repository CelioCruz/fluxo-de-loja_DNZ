import streamlit as st
from fpdf import FPDF
import base64
import io
from datetime import datetime
from google_planilha import GooglePlanilha


def tela_exame_vista():
    """Tela de encaminhamento para exame oftalmológico."""
    st.subheader("🩺 ENCAMINHAMENTO")

    # Inicializa campos no session_state
    _inicializar_session_state()

    # Campo: Nome do Paciente
    cliente_input = st.text_input(
        "Nome do Paciente",
        value=st.session_state.enc_cliente,
        key="enc_cliente_input"
    ).strip().upper()
    st.session_state.enc_cliente = cliente_input

    # Campo: Telefone
    telefone_input = st.text_input(
        "Telefone",
        value=st.session_state.enc_telefone,
        placeholder="(00) 00000-0000",
        key="enc_telefone_input"
    )
    st.session_state.enc_telefone = telefone_input

    # Campo: Data de Nascimento
    nascimento_input = st.text_input(
        "Data de Nascimento",
        value=st.session_state.enc_nascimento,
        placeholder="DD/MM/AAAA",
        key="enc_nascimento_input"
    )
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
    vendedores = _carregar_vendedores()
    if not vendedores:
        return

    # Seleciona vendedor
    if st.session_state.enc_vendedor in vendedores:
        index_vendedor = vendedores.index(st.session_state.enc_vendedor)
    else:
        index_vendedor = 0

    st.session_state.enc_vendedor = st.selectbox(
        "Vendedor que encaminhou",
        options=vendedores,
        index=index_vendedor,
        key="sel_vendedor_enc"
    )

    st.markdown("---")

    # Botões: Gerar PDF e Voltar
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🖨️ GERAR PDF", use_container_width=True):
            with st.spinner("Gerando PDF..."):
                pdf_buffer = gerar_pdf_em_memoria()
                if pdf_buffer:
                    st.success("✅ PDF gerado com sucesso!")
                    exibir_pdf_no_navegador(pdf_buffer)
                    st.session_state.pdf_gerado = True
                else:
                    st.error("❌ Falha ao gerar PDF.")

    with col2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa = 'atendimento'
            st.session_state.subtela = ''
            st.rerun()

    # Botão: Concluído – Voltar à loja
    if st.session_state.get('pdf_gerado', False):
        st.markdown("---")
        if st.button("✅ Concluído – Voltar à loja", use_container_width=True):
            _limpar_dados_encaminhamento()
            st.session_state.etapa = 'loja'
            st.rerun()


# === FUNÇÕES AUXILIARES ===
def _inicializar_session_state():
    """Inicializa variáveis no session_state."""
    defaults = {
        'enc_cliente': "",
        'enc_telefone': "",
        'enc_nascimento': "",
        'enc_vendedor': "",
        'enc_tipo': "PARTICULAR",
        'pdf_gerado': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _carregar_vendedores():
    """Carrega lista de vendedores da loja atual."""
    try:
        if 'gsheets' not in st.session_state:
            st.session_state.gsheets = GooglePlanilha()
        gsheets = st.session_state.gsheets
        vendedores_data = gsheets.get_vendedores_por_loja()
        return [v['VENDEDOR'] for v in vendedores_data] if vendedores_data else []
    except Exception as e:
        st.error(f"❌ Erro ao carregar vendedores: {str(e)}")
        return []


def _limpar_dados_encaminhamento():
    """Limpa os dados de encaminhamento do session_state."""
    chaves = [
        'enc_cliente', 'enc_telefone', 'enc_nascimento',
        'enc_vendedor', 'enc_tipo', 'pdf_gerado'
    ]
    for key in chaves:
        if key in st.session_state:
            del st.session_state[key]


# === GERAÇÃO DE PDF EM MEMÓRIA ===
def gerar_pdf_em_memoria():
    """Gera o PDF com validação e suporte a acentos"""
    try:
        # ✅ Validação dos dados
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

        # ✅ Cria buffer em memória
        pdf_buffer = io.BytesIO()  # ← Use BytesIO, não BytesIO

        # ✅ Configura o FPDF
        pdf = FPDF(format='A4', unit='mm', orientation='P')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ✅ Fonte padrão
        pdf.set_font("Arial", 'B', 16)

        # ✅ Título centralizado
        pdf.cell(0, 10, "ENCAMINHAMENTO", ln=True, align='C')
        pdf.ln(10)

        # ✅ Função para adicionar campo
        def add_item(label, value):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(40, 8, f"{label}:", 0, 0)
            pdf.set_font("Arial", '', 12)
            text = str(value) if value else ""
            # Trata acentos (usando latin1)
            try:
                text = text.encode('latin1', 'replace').decode('latin1')
            except AttributeError:
                # Se for bytearray, já é binário
                pass
            pdf.cell(0, 8, f" {text}", ln=True)
            pdf.set_x(10)

        # ✅ Dados do paciente
        add_item("Paciente", st.session_state.enc_cliente)
        add_item("Telefone", formatar_telefone(st.session_state.enc_telefone))
        add_item("Nascimento", formatar_data_nascimento(st.session_state.enc_nascimento))
        add_item("Atendimento", st.session_state.enc_tipo)

        # ✅ Assinatura
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 6, "Consultor", ln=True, align='C')
        pdf.cell(0, 6, st.session_state.enc_vendedor, ln=True, align='C')

        # --- MENSAGEM FINAL ---
        pdf.ln(15)
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(50, 50, 50)

        nome_cliente = st.session_state.enc_cliente.strip()
        if not nome_cliente:
            nome_cliente = "Cliente"

        tratamento = "Sra." if nome_cliente.split()[-1].endswith('a') and len(nome_cliente.split()[-1]) > 1 else "Sr."

        data_hoje = datetime.now().strftime("%d/%m/%Y")
        mensagem_final = f"Hoje ({data_hoje}), encaminhamento para exame oftalmológico."
        pdf.cell(0, 8, mensagem_final, ln=True, align='L')

        # ✅ Gera o PDF como bytes e escreve diretamente no buffer
        pdf_output = pdf.output(dest='S')  # → bytearray ou bytes
        pdf_buffer.write(pdf_output)  # ← Escreve diretamente

        pdf_buffer.seek(0)
        return pdf_buffer

    except Exception as e:
        st.error(f"❌ Erro ao gerar PDF: {str(e)}")
        return None


def formatar_telefone(tel):
    """Formata telefone para (XX) XXXXX-XXXX ou (XX) XXXX-XXXX"""
    if not tel:
        return ""
    tel = ''.join(filter(str.isdigit, tel))
    if len(tel) == 11:
        return f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"
    elif len(tel) == 10:
        return f"({tel[:2]}) {tel[2:6]}-{tel[6:]}"
    return tel


def formatar_data_nascimento(data):
    """Formata data de nascimento para DD/MM/AAAA"""
    if not data:
        return ""
    
    # Remove tudo que não for número
    data = ''.join(filter(str.isdigit, data))
    
    # Se tiver 6 dígitos (DDMMYY), ou 8 dígitos (DDMMYYYY)
    if len(data) == 6:
        dia = data[:2]
        mes = data[2:4]
        ano = "20" + data[4:] if data[4:] < "30" else "19" + data[4:]
    elif len(data) == 8:
        dia = data[:2]
        mes = data[2:4]
        ano = data[4:]
    else:
        return data  # Não pode ser formatado

    return f"{dia}/{mes}/{ano}"


def exibir_pdf_no_navegador(pdf_buffer):
    """Exibe o PDF com botão de download nomeado pelo cliente"""
    try:
        nome_cliente = st.session_state.enc_cliente.strip()
        if not nome_cliente:
            nome_cliente = "encaminhamento"

        nome_arquivo = "".join(c for c in nome_cliente.upper() if c.isalnum() or c in " _-").strip()
        nome_arquivo += ".pdf"

        pdf_buffer.seek(0)

        st.download_button(
            label="📥 Baixar PDF",
            data=pdf_buffer,
            file_name=nome_arquivo,
            mime="application/pdf",
            key="download_pdf_unico"
        )

        st.success(f"✅ PDF gerado com sucesso! Pronto para baixar como: **{nome_arquivo}**")

    except Exception as e:
        st.error(f"❌ Erro ao exibir PDF: {str(e)}")