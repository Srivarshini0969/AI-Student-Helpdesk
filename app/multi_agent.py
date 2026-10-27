import asyncio, re
from app.config import ENABLE_AUTOGEN, OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL

try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.ollama import OllamaChatCompletionClient
    AUTOGEN_OK = True
except Exception as import_error:
    AUTOGEN_OK = False
    AUTOGEN_ERROR = str(import_error)

def fallback(question, matches, note="Fallback review"):
    terms = ["college","student","exam","attendance","fee","certificate","bonafide","course registration","library","semester","hostel","academic","department","timetable","transfer"]
    return {
        "in_scope": any(t in question.lower() for t in terms),
        "scope_review": note,
        "evidence_sufficient": bool(matches),
        "evidence_review": "Evidence presence used as fallback.",
        "agent_mode": "fallback"
    }

async def _review(question, evidence):
    client = OllamaChatCompletionClient(model=OLLAMA_CHAT_MODEL, host=OLLAMA_BASE_URL)
    try:
        scope = AssistantAgent(
            name="QueryScopeAgent", model_client=client,
            system_message="Classify a question as student-helpdesk related. Reply exactly: IN_SCOPE: YES or NO; REASON: short sentence. Do not answer."
        )
        scope_result = await scope.run(task=f"Question: {question}")
        scope_text = str(scope_result.messages[-1].content)
        in_scope = not bool(re.search(r"IN_SCOPE:\s*NO", scope_text, re.I))
        reviewer = AssistantAgent(
            name="EvidenceReviewAgent", model_client=client,
            system_message="Review if evidence supports the question. Reply exactly: EVIDENCE: SUFFICIENT or INSUFFICIENT; REASON: short sentence. Do not answer."
        )
        result = await reviewer.run(task=f"Question: {question}\nEvidence:\n{evidence[:6000]}")
        evidence_text = str(result.messages[-1].content)
        sufficient = not bool(re.search(r"EVIDENCE:\s*INSUFFICIENT", evidence_text, re.I))
        return {"in_scope": in_scope, "scope_review": scope_text[:500], "evidence_sufficient": sufficient, "evidence_review": evidence_text[:500], "agent_mode": "autogen"}
    finally:
        await client.close()

def review_with_agents(question, matches):
    evidence = "\n\n".join(f"Source: {m['source']}\n{m['text']}" for m in matches)
    if not ENABLE_AUTOGEN:
        return fallback(question, matches, "AutoGen disabled")
    if not AUTOGEN_OK:
        return fallback(question, matches, f"AutoGen import failed: {AUTOGEN_ERROR}")
    try:
        return asyncio.run(_review(question, evidence))
    except Exception as exc:
        return fallback(question, matches, f"AutoGen runtime failed; fallback used: {exc}")
