import os
import streamlit as st
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from openai import OpenAI

load_dotenv()

doc_client = DocumentIntelligenceClient(
    endpoint=os.getenv("AZURE_DOCUMENT_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_DOCUMENT_KEY"))
)

openai_client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN"),
)
MODEL_NAME = "gpt-4o"

def extraer_texto_pdf(archivo_bytes):
    poller = doc_client.begin_analyze_document(
        "prebuilt-layout", 
        body=archivo_bytes, 
        content_type="application/octet-stream"
    )
    result = poller.result()
    return result.content

def analizar_contrato(texto_contrato):
    prompt_sistema = """
    Eres un abogado auditor experto. Tu trabajo es analizar exhaustivamente el contrato que te voy a proporcionar.
    
    ESTRUCTURA DE TU RESPUESTA:
    🚨 0. ADVERTENCIA DE LEGALIDAD: Evalúa si hay cláusulas ilegales, abusivas o extremadamente desproporcionadas (ej. penalizaciones abusivas, intereses de usura, renuncias de derechos fundamentales). Si las hay, ponlas AQUÍ AL PRINCIPIO DEL TODO destacadas en rojo o con emojis de alerta y explica por qué son abusivas. Si no detectas ninguna, omite este punto cero.
    
    Luego, continúa con el resumen estándar:
    1. Propósito principal del contrato.
    2. Fechas clave (Inicio, fin, renovación, preavisos).
    3. Cláusulas de penalización o riesgos económicos generales.
    4. Nivel de Riesgo General (Bajo, Medio, Alto) con una breve justificación.
    
    Responde siempre en español, de forma muy profesional y clara.
    """
    
    respuesta = openai_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"Analiza este contrato:\n\n{texto_contrato}"}
        ],
        temperature=0.2 
    )
    return respuesta.choices[0].message.content

st.set_page_config(page_title="Agente Legal IA", page_icon="⚖️")

st.title("⚖️ Agente Analista de Contratos Legales")
st.write("Sube un contrato en formato PDF. La IA extraerá el texto, advertirá de cláusulas abusivas y generará un informe de riesgos.")

archivo_subido = st.file_uploader("Sube tu contrato (PDF)", type=["pdf"])

if archivo_subido is not None:
    if st.button("Analizar Contrato"):
        with st.spinner("Leyendo y estructurando el documento con Azure Document Intelligence..."):
            bytes_pdf = archivo_subido.read()
            texto_extraido = extraer_texto_pdf(bytes_pdf)
            
        with st.spinner("Analizando riesgos y cláusulas con la IA..."):
            analisis_legal = analizar_contrato(texto_extraido)
            
        st.success("¡Análisis completado!")
        
        tab1, tab2 = st.tabs(["📝 Análisis Legal", "📄 Texto Extraído (Raw)"])
        
        with tab1:
            st.markdown(analisis_legal)
            
        with tab2:
            st.text_area("Texto tal como lo entendió la IA:", value=texto_extraido, height=300)