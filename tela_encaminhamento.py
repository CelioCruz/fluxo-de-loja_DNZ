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
    try:
        if 'gsheets' not in st.session_state:
            st.session_state.gsheets = GooglePlanilha()
        gsheets = st.session_state.gsheets
        vendedores_data = gsheets.get_vendedores_por_loja()
        vendedores = [v['VENDEDOR'] for v in vendedores_data] if vendedores_data else []
    except Exception as e:
        st.error(f"❌ Erro ao carregar vendedores: {str(e)}")
        return

    if not vendedores:
        st.warning("⚠️ Nenhum vendedor encontrado.")
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

    # Botões: Visualizar e Voltar
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🖨️ VISUALIZAR", use_container_width=True):
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
            chaves_limpar = [
                'enc_cliente', 'enc_telefone', 'enc_nascimento',
                'enc_vendedor', 'enc_tipo', 'pdf_gerado'
            ]
            for key in chaves_limpar:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.etapa = 'loja'
            st.rerun()


# === FUNÇÕES AUXILIARES ===
def formatar_telefone(tel):
    """Formata telefone para (XX) XXXXX-XXXX ou (XX) XXXX-XXXX"""
    if not tel:
        return ""
    # Remove tudo que não for número
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
    data = data.strip()
    partes = data.split('/')
    if len(partes) == 3:
        try:
            dia = partes[0].zfill(2)
            mes = partes[1].zfill(2)
            ano = partes[2]
            if len(ano) == 2:
                ano = "20" + ano if ano < "30" else "19" + ano
            return f"{dia}/{mes}/{ano}"
        except:
            pass
    return data


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
        pdf_data = pdf.output(dest='S').encode('utf-8')  # Garante bytes
        pdf_buffer.write(pdf_data)
        pdf_buffer.seek(0)

        return pdf_buffer

    except Exception as e:
        st.error(f"❌ Erro ao gerar PDF: {str(e)}")
        return None  # Retorna None em vez de levantar, para não quebrar


# === EXIBIÇÃO DO PDF EM TELA (SEM DOWNLOAD) ===
def exibir_pdf_no_navegador(pdf_buffer):
    """Exibe o PDF diretamente no navegador usando HTML seguro"""
    try:
        pdf_buffer.seek(0)
        b64_pdf = base64.b64encode(pdf_buffer.read()).decode()

        # Usa st.components.v1.html para exibir o PDF com controle total
        pdf_display = f"""
        <div style="width:100%; text-align:center; margin-bottom:10px;">
            <h4>Encaminhamento - Pronto para impressão</h4>
        </div>
        <embed src="data:application/pdf;base64,{b64_pdf}" 
               width="100%" 
               height="600px" 
               type="application/pdf"
               style="border: 1px solid #ddd; border-radius: 8px;">
        <div style="text-align: center; margin: 20px 0;">
            <button onclick="window.open('data:application/pdf;base64,{b64_pdf}')" 
                    style="background-color: #007BFF; color: white; border: none; padding: 12px 24px; 
                           border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold;">
                🖨️ Abrir em nova aba e imprimir
            </button>
        </div>
        """

        st.markdown(pdf_display, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Erro ao exibir PDF: {str(e)}")