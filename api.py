from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
from rag.embedder import client, embedding_model, CHROMA_PATH
from langchain_community.vectorstores import Chroma

app = Flask(__name__)
CORS(app)

# Load the existing vector database
vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "edulite-ai"})

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "").strip()
    grade = data.get("grade", "middle")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # 1. Search the PDFs for relevant context
    docs = vector_db.similarity_search(question, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    # 2. Build the prompt — THIS WAS MISSING
    grade_instructions = {
        "primary": "Explain simply for a young child aged 6-10. Use very short sentences.",
        "middle": "Explain clearly for a student aged 11-13. Use correct subject terms.",
        "high": "Give a detailed accurate answer for a board exam student aged 14-16."
    }
    instruction = grade_instructions.get(grade, grade_instructions["middle"])

    prompt = f"""{instruction}

Use ONLY the following textbook content to answer the question.
If the answer is not in the content below, say "I don't have that in my textbooks."

Textbook content:
---
{context}
---

Student question: {question}

Answer:"""

    # 3. Send to Ollama
    response = ollama.chat(model='edulite-ai', messages=[
        {'role': 'user', 'content': prompt},
    ])

    return jsonify({
        "answer": response['message']['content'],
        "sources": [doc.metadata.get('source') for doc in docs]
    })

@app.route("/quiz", methods=["POST"])
def quiz():
    data = request.json
    subject = data.get("subject", "Science")
    grade = data.get("grade", "middle")
    num = data.get("num_questions", 5)
    grade_level = {"primary": "Class 1-5", "middle": "Class 6-8", "high": "Class 9-10"}.get(grade, "Class 8")

    prompt = f"""Generate {num} multiple choice questions for CBSE {grade_level} students on {subject}.

Format EXACTLY like this for each question:
Q: [question text]
A) [option 1]
B) [option 2]
C) [option 3]
D) [option 4]
Answer: [A or B or C or D]

Generate {num} questions now:"""

    response = ollama.chat(model='edulite-ai', messages=[
        {'role': 'user', 'content': prompt}
    ])

    return jsonify({"questions": response['message']['content'], "subject": subject})

if __name__ == "__main__":
    print("EduLite AI API starting on port 5001...")
    app.run(host="0.0.0.0", port=5001)
