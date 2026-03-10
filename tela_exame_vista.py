import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
from google_planilha import GooglePlanilha

def mostrar():
    """Tela de encaminhamento para exame oftalmológico."""
    st.subheader("🩺 ENCAMINHAMENTO")

    # Inicializa campos no session_state
    _inicializar_session_state()

    # Layout em colunas para os dados do paciente
    col_a, col_b = st.columns(2)
    
    with col_a:
        cliente_input = st.text_input(
            "Nome do Paciente",
            value=st.session_state.enc_cliente,
            key="enc_cliente_input"
        ).strip().upper()
        st.session_state.enc_cliente = cliente_input

        telefone_input = st.text_input(
            "Telefone",
            value=st.session_state.enc_telefone,
            placeholder="(00) 00000-0000",
            key="enc_telefone_input"
        )
        st.session_state.enc_telefone = telefone_input

    with col_b:
        nascimento_input = st.text_input(
            "Data de Nascimento",
            value=st.session_state.enc_nascimento,
            placeholder="DD/MM/AAAA",
            key="enc_nascimento_input"
        )
        st.session_state.enc_nascimento = nascimento_input

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
        st.warning("⚠️ Carregando vendedores...")
        vendedores = ["NENHUM"]

    # Seleciona vendedor
    idx_vend = 0
    if st.session_state.enc_vendedor in vendedores:
        idx_vend = vendedores.index(st.session_state.enc_vendedor)

    st.session_state.enc_vendedor = st.selectbox(
        "Vendedor que encaminhou",
        options=vendedores,
        index=idx_vend,
        key="sel_vendedor_enc"
    )

    st.markdown("---")

    # Botões: Gerar PDF e Voltar
    c1, c2 = st.columns(2)

    with c1:
        if st.button("🖨️ GERAR ENCAMINHAMENTO", use_container_width=True, type="primary"):
            if not st.session_state.enc_cliente:
                st.error("⚠️ O nome do paciente é obrigatório.")
            else:
                with st.spinner("Gerando documento..."):
                    pdf_bytes = gerar_pdf_bytes()
                    if pdf_bytes:
                        st.session_state.pdf_bytes = pdf_bytes
                        st.session_state.pdf_gerado = True
                        st.success("✅ Documento pronto!")
                    else:
                        st.error("❌ Erro ao gerar o arquivo PDF.")

    with c2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa = 'atendimento'
            st.session_state.subtela = ''
            st.rerun()

    # Se o PDF foi gerado, mostra o botão de download
    if st.session_state.get('pdf_gerado') and 'pdf_bytes' in st.session_state:
        st.markdown("---")
        nome_arquivo = f"ENCAMINHAMENTO_{st.session_state.enc_cliente.replace(' ', '_')}.pdf"
        
        st.download_button(
            label="📥 BAIXAR E IMPRIMIR PDF",
            data=st.session_state.pdf_bytes,
            file_name=nome_arquivo,
            mime="application/pdf",
            use_container_width=True,
            key="btn_download_final"
        )
        
        if st.button("✅ Concluído – Voltar à loja", use_container_width=True):
            _limpar_dados_encaminhamento()
            st.session_state.etapa = 'loja'
            st.rerun()


def _inicializar_session_state():
    for key, val in {
        'enc_cliente': "", 'enc_telefone': "", 'enc_nascimento': "",
        'enc_vendedor': "", 'enc_tipo': "PARTICULAR", 'pdf_gerado': False
    }.items():
        if key not in st.session_state: st.session_state[key] = val

def _carregar_vendedores():
    try:
        if 'gsheets' not in st.session_state: st.session_state.gsheets = GooglePlanilha()
        vends = st.session_state.gsheets.get_vendedores_por_loja()
        return [v['VENDEDOR'] for v in vends] if vends else []
    except: return []

def _limpar_dados_encaminhamento():
    for k in ['enc_cliente', 'enc_telefone', 'enc_nascimento', 'enc_vendedor', 'enc_tipo', 'pdf_gerado', 'pdf_bytes']:
        if k in st.session_state: del st.session_state[k]

def formatar_telefone(tel):
    tel = ''.join(filter(str.isdigit, str(tel)))
    if len(tel) == 11: return f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"
    if len(tel) == 10: return f"({tel[:2]}) {tel[2:6]}-{tel[6:]}"
    return tel

def formatar_data(data):
    d = ''.join(filter(str.isdigit, str(data)))
    if len(d) == 8: return f"{d[:2]}/{d[2:4]}/{d[4:]}"
    return data

def gerar_pdf_bytes():
    try:
        # Usamos fpdf2 (ou fpdf padrão)
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Título
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 20, "ENCAMINHAMENTO EXAME", ln=True, align='C')
        pdf.ln(10)
        
        # Dados do Paciente
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, " DADOS DO PACIENTE", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Paciente: {st.session_state.enc_cliente}", ln=True)
        pdf.cell(0, 8, f"Nascimento: {formatar_data(st.session_state.enc_nascimento)}", ln=True)
        pdf.cell(0, 8, f"Telefone: {formatar_telefone(st.session_state.enc_telefone)}", ln=True)
        pdf.cell(0, 8, f"Atendimento: {st.session_state.enc_tipo}", ln=True)
        pdf.ln(10)
        
        # Encaminhado por
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, " RESPONSÁVEL PELO ENCAMINHAMENTO", ln=True, fill=True)
        pdf.ln(2)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Consultor(a): {st.session_state.enc_vendedor}", ln=True)
        pdf.cell(0, 8, f"Loja: {st.session_state.get('loja', 'NÃO INFORMADA')}", ln=True)
        pdf.cell(0, 8, f"Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", ln=True)
        
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(0, 5, "Este documento é um encaminhamento formal para a realização de exame oftalmológico. Favor apresentar este formulário na recepção da clínica.", align='C')

        # Retorna os bytes diretamente
        return pdf.output()

    except Exception as e:
        print(f"Erro PDF: {e}")
        return None
