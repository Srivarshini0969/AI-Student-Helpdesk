from pathlib import Path
import requests
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from app.config import DOCUMENTS_DIR, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, TOP_K

class StudentDocumentRAG:
    def __init__(self):
        self.index = None
        self.documents_loaded = 0

    def rebuild(self):
        folder = Path(DOCUMENTS_DIR)
        folder.mkdir(parents=True, exist_ok=True)
        files = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf",".txt",".md",".docx"}]
        if not files:
            self.index = None
            self.documents_loaded = 0
            return {"ok": False, "message": "No documents found. Add college PDFs/TXT/MD/DOCX files to data/documents."}
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m.get("name","") for m in r.json().get("models", [])]
        if not any(m.split(":")[0] == OLLAMA_EMBED_MODEL.split(":")[0] for m in models):
            raise RuntimeError(f"Embedding model missing. Run: ollama pull {OLLAMA_EMBED_MODEL}")
        Settings.embed_model = OllamaEmbedding(model_name=OLLAMA_EMBED_MODEL, base_url=OLLAMA_BASE_URL)
        docs = SimpleDirectoryReader(input_dir=str(folder), recursive=True, required_exts=[".pdf",".txt",".md",".docx"]).load_data()
        if not docs:
            self.index = None
            return {"ok": False, "message": "Files found, but no readable text was extracted."}
        self.index = VectorStoreIndex.from_documents(docs)
        self.documents_loaded = len(docs)
        return {"ok": True, "documents": self.documents_loaded, "message": "Index rebuilt successfully."}

    def retrieve(self, question):
        if self.index is None:
            return []
        nodes = self.index.as_retriever(similarity_top_k=TOP_K).retrieve(question)
        out = []
        for item in nodes:
            node = item.node
            meta = node.metadata or {}
            out.append({"text": node.get_content(), "source": Path(str(meta.get("file_name") or meta.get("file_path") or "unknown")).name, "score": float(item.score or 0)})
        return out

rag_engine = StudentDocumentRAG()
