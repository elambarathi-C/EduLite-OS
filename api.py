from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
from rag.embedder import client, embedding_model, CHROMA_PATH
from langchain_community.vectorstores import Chroma

app = Flask(__name__)
CORS(app)

# Load the existing vector database
vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")
    
    # 1. Search the PDFs for relevant context
    docs = vector_db.similarity_search(question, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    
    # 2. Send context + question to Ollama (TinyLlama)
    prompt = f"Using this context: {context}\n\nAnswer this: {question}"
    
    response = ollama.chat(model='tinyllama', messages=[
        {'role': 'user', 'content': prompt},
    ])
    
    return jsonify({
        "answer": response['message']['content'],
        "sources": [doc.metadata.get('source') for doc in docs]
    })

if __name__ == "__main__":
    print("EduLite AI API starting on port 5001...")
    app.run(host="0.0.0.0", port=5001)