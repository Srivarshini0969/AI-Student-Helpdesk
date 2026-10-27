from flask import Flask, jsonify, render_template, request
import requests
from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL, MIN_RETRIEVAL_SCORE
from app.rag_engine import rag_engine
from app.multi_agent import review_with_agents
from app.qa_chain import generate_answer

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

@app.get("/")
def index():
    return render_template("index.html", chat_model=OLLAMA_CHAT_MODEL, embed_model=OLLAMA_EMBED_MODEL)

@app.get("/api/health")
def health():
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=4); r.raise_for_status()
        return jsonify({"ok": True, "ollama_url": OLLAMA_BASE_URL, "chat_model": OLLAMA_CHAT_MODEL,
                        "embedding_model": OLLAMA_EMBED_MODEL, "installed_models": [m.get("name","") for m in r.json().get("models",[])],
                        "index_ready": rag_engine.index is not None, "document_chunks": rag_engine.documents_loaded})
    except requests.RequestException as exc:
        return jsonify({"ok": False, "error": str(exc)}), 503

@app.post("/api/reindex")
def reindex():
    try:
        result = rag_engine.rebuild()
        return jsonify(result), 200 if result.get("ok") else 400
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    question = str(body.get("question","")).strip()
    if not question: return jsonify({"error":"Please enter a question."}), 400
    if len(question) > 1500: return jsonify({"error":"Please keep the question under 1500 characters."}), 400
    if rag_engine.index is None:
        return jsonify({"answer":"The document index is not ready. Add college documents to data/documents and click Rebuild Index.","sources":[],"agent_mode":"not_started"}), 400
    try:
        matches = rag_engine.retrieve(question)
        if matches and matches[0]["score"] < MIN_RETRIEVAL_SCORE: matches = []
        review = review_with_agents(question, matches)
        if not review.get("in_scope", True):
            answer = "This question appears outside the student-helpdesk scope. Ask about college academics, fees, exams, certificates, or campus services."
            mode = "scope_check"
        elif not matches or not review.get("evidence_sufficient", False):
            answer = "I could not find sufficient supporting information in the provided college documents. Please contact the relevant college office."
            mode = "insufficient_evidence"
        else:
            answer = generate_answer(question, matches)
            mode = "langchain_rag"
        return jsonify({"answer":answer,"sources":[{"filename":m["source"],"score":round(m["score"],3),"excerpt":m["text"][:450]} for m in matches],
                        "agent_mode":review.get("agent_mode"),"agent_review":review,"mode":mode})
    except Exception as exc:
        return jsonify({"error":f"Question processing failed: {exc}"}), 500

if __name__ == "__main__":
    print("Starting AI Student Helpdesk...")
    print(f"Chat model: {OLLAMA_CHAT_MODEL} | Embedding model: {OLLAMA_EMBED_MODEL}")
    try:
        print(rag_engine.rebuild())
    except Exception as exc:
        print(f"Initial index build failed: {exc}")
        print("Add documents, start Ollama, and use Rebuild Index after startup.")
    app.run(host="127.0.0.1", port=5000, debug=True)
