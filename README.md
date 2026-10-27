# AI-Based Student Helpdesk — Agentic RAG Prototype

This project implements the architecture described in the case-study PDF:
- **LlamaIndex** loads PDF/TXT/MD/DOCX college documents, creates a vector index, and retrieves relevant passages.
- **LangChain** builds a grounded QA prompt and calls the local Qwen model.
- **AutoGen** coordinates two agents: `QueryScopeAgent` checks whether a question is within the student-helpdesk domain; `EvidenceReviewAgent` reviews whether retrieved evidence appears relevant.
- **Ollama** runs the chat and embedding models locally.
- **Flask** serves the browser-based chatbot.

The intended workflow is question → agent review → LlamaIndex retrieval → LangChain QA pipeline → Qwen/Ollama → answer. The case-study PDF also asks for architecture, college documents, a working chatbot, at least 10 sample questions, evaluation, and a short report.

## Important
The included `demo_student_handbook.txt` is fictional demonstration text, not official college policy. Replace it with approved college handbooks, regulations, notices, circulars, and FAQs before claiming answers represent actual college rules. The assignment PDF is a design brief, not a policy source.

## Setup (Windows / VS Code / PowerShell)
Python 3.11 or 3.12 is recommended for package compatibility. Install Ollama separately.

1. Open this folder in VS Code and open Terminal → New Terminal.
2. Create and activate the virtual environment:
```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
```
If PowerShell blocks activation in this terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& ".\.venv\Scripts\Activate.ps1"
```
3. Install Python packages:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```
4. Create configuration:
```powershell
Copy-Item .env.example .env
```
5. Pull local models once:
```powershell
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama list
```
Qwen generates answers. `nomic-embed-text` creates embeddings used by LlamaIndex for semantic retrieval.
6. Add approved college PDF/TXT/MD/DOCX files to `data/documents`.
7. Start the app:
```powershell
python -m app.main
```
or `.un.ps1`
8. Open http://127.0.0.1:5000. Click **Rebuild Index** after changing documents.

## Useful checks
```powershell
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

## Suggested questions
1. What is the procedure for applying for a bonafide certificate?
2. What documents are required for examination registration?
3. What is the attendance requirement?
4. How can a fee receipt be obtained?
5. What are the library timings?
6. What is the last date for course registration?
7. What is the procedure for applying for a transfer certificate?
8. Where can I find information about semester registration?
9. Which document explains academic regulations?
10. What should I do if the documents do not cover my question?

## Limitations
- Academic prototype, not an official college service.
- The app does not perform live internet search.
- AutoGen is a small two-agent review workflow. If AutoGen import/runtime fails, a fallback is used; inspect `agent_mode` and agent review details rather than claiming agents ran when the response says `fallback`.
- Retrieval depends on the quality of source documents and embedding model.
- Index is built in memory at startup; rebuild it after adding or updating documents.
- AutoGen and LangChain each call the local chat model, so a response can take time on lower-memory computers.
