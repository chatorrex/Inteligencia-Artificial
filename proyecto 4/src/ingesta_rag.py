import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Configuración de rutas
CORPUS_DIR = "./data/corpus"
VECTOR_DB_DIR = "./data/vector_store"

def procesar_y_vectorizar():
    print("1. Cargando documentos del corpus...")
    # Asegurar que existan las carpetas
    os.makedirs(CORPUS_DIR, exist_ok=True)
    
    if not os.listdir(CORPUS_DIR):
        print(f"⚠️ Alerta: Coloca documentos PDF o TXT en la carpeta '{CORPUS_DIR}' antes de correr.")
        return

    loader = PyPDFDirectoryLoader(CORPUS_DIR)
    documentos = loader.load()
    print(f"Total de páginas/documentos cargados: {len(documentos)}")

    print("\n2. Segmentando texto (Chunking)...")
    # Configuración optimizada para balancear precisión y contexto
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(documentos)
    print(f"Total de fragmentos (chunks) generados: {len(chunks)}")

    print("\n3. Generando Embeddings y Base de Datos Vectorial...")
    # Usamos un modelo open-source muy ligero (bge-small o all-MiniLM-L6-v2) ideal para CPU
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'}
    )

    # Crear y persistir la base de datos ChromaDB
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR
    )
    vector_db.persist()
    print(f"✅ Base de datos vectorial guardada exitosamente en: {VECTOR_DB_DIR}")

if __name__ == "__main__":
    procesar_y_vectorizar()