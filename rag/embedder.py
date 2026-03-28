import os
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Windows-compatible path logic
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# Initialize the Chroma client
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Define the embedding model
# Note: Adarshini needs 'sentence-transformers' installed via pip
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def index_pdfs(pdf_folder):
    """Chunks PDFs and saves them to the local vector database."""
    documents = []
    for root, dirs, files in os.walk(pdf_folder):
        for file in files:
            if file.endswith(".pdf"):
                path = os.path.join(root, file)
                loader = PyPDFLoader(path)
                documents.extend(loader.load())

    # Split text into manageable pieces
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    # Create/Update the vector store
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_PATH
    )
    print(f"Successfully indexed {len(chunks)} chunks to {CHROMA_PATH}")

if __name__ == "__main__":
    # Test indexing if run directly
    pdf_dir = os.path.join(BASE_DIR, "content", "pdfs")
    index_pdfs(pdf_dir)