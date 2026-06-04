import time
import ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

VECTOR_DB_DIR = "./data/vector_store"
MODELO_OLLAMA = "phi3:mini" 

# Configurar el mismo embedding de la ingesta
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={'device': 'cpu'})

# Cargar base vectorial
try:
    vector_db = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
    # Verificamos rápidamente si contiene datos
    if len(vector_db.get()['ids']) == 0:
        print("⚠️ Alerta: La base de datos vectorial existe pero parece no tener datos.")
except Exception as e:
    print(f"❌ Error al cargar la base de datos vectorial: {str(e)}")
    print("Asegúrate de haber ejecutado 'src/ingesta_rag.py' primero.")
    exit()

# Prompt del Sistema que simula/refuerza el comportamiento del Fine-Tuning solicitado
SYSTEM_PROMPT = """Eres un Tutor Inteligente y Analítico especializado en seguridad pública y violencia en México.
Tu comportamiento debe regirse estrictamente por las siguientes reglas académicas:
1. TONO ACADÉMICO: Mantén absoluta neutralidad, objetividad y rigor conceptual. Evita sesgos emocionales.
2. CITAR FUENTES: Al responder, incluye de forma explícita referencias al final de tus oraciones o párrafos indicando de qué fragmento del corpus provienen (ej. [Documento Fuente: Nombre/ID]).
3. MÉTODO SOCRÁTICO: No des conclusiones digeridas en temas de análisis profundo. Formula preguntas analíticas para guiar la reflexión del usuario.
4. MANEJO DE INCERTIDUMBRE (MITIGACIÓN DE ALUCINACIONES): Si el contexto recuperado no contiene la información exacta para responder la pregunta, di textualmente: "La información proporcionada en el corpus no detalla este aspecto" y niégate a especular.

Usa UNICAMENTE el siguiente contexto recuperado para responder la pregunta del usuario:
---------------------
{contexto}
---------------------
"""

def consultar_tutor_rag(pregunta_usuario):
    inicio_tiempo = time.time()
    
    # 1. Recuperación Semántica (RAG) - Top-K = 3 para no saturar tu CPU
    docs_recuperados = vector_db.similarity_search(pregunta_usuario, k=3)
    
    # Construir el bloque de contexto y guardar los chunks recuperados para auditoría
    contexto_str = ""
    chunks_auditoria = []
    for i, doc in enumerate(docs_recuperados):
        origen = doc.metadata.get('source', f'Documento Ficticio {i+1}')
        texto_limpio = doc.page_content.replace('\n', ' ')
        contexto_str += f"\n[Fragmento {i+1} - Fuente: {origen}]: {texto_limpio}\n"
        chunks_auditoria.append((origen, texto_limpio))
        
    # 2. Generación con Ollama (LLM)
    prompt_sistema_inyectado = SYSTEM_PROMPT.format(contexto=contexto_str)
    
    try:
        response = ollama.chat(model=MODELO_OLLAMA, messages=[
            {"role": "system", "content": prompt_sistema_inyectado},
            {"role": "user", "content": pregunta_usuario}
        ])
        respuesta_final = response['message']['content']
    except Exception as e:
        respuesta_final = f"Error al conectar con Ollama: {str(e)}"
        
    latencia = time.time() - inicio_tiempo
    
    return respuesta_final, chunks_auditoria, latencia

banco_preguntas = {
    "Pregunta 1: ": "¿Cuantos archivos tienes registrados en el corpus?",
    "Pregunta 2: ": "¿Cuantos autorres distintos manejas?",
    "Pregunta 3: ": "¿Que piensa la autora Mariana Campos sobre la violencia en mexico?"
}

if __name__ == "__main__":
    print(f"🤖 Iniciando Banco de Pruebas del Tutor Analítico Híbrido en Modelo: '{MODELO_OLLAMA}'...\n")
    
    for nivel, pregunta in banco_preguntas.items():
        print("="*80)
        print(f"📌 {nivel}")
        print(f"Pregunta: {pregunta}")
        print("="*80)
        
        respuesta, chunks, tiempo = consultar_tutor_rag(pregunta)
        
        print(f"\n⏱️ LATENCIA: {tiempo:.2f} segundos")
        print("\n🔍 CHUNKS RECUPERADOS (Justificación):")
        for idx, (fuente, texto) in enumerate(chunks):
            print(f"  • [{idx+1}] Fuente: {fuente} | Texto: {texto[:120]}...")
            
        print("\n🎓 RESPUESTA DEL TUTOR:")
        print(respuesta)
        print("\n" + "-"*80 + "\n")