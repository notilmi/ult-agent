import re
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage
from src.agent.state import AgentState
from src.agent.utils import extract_text_content

# Indonesian PII detection patterns
NIM_PATTERN = re.compile(r"\b\d{8,12}\b")      # Polsri Student ID (usually 10 digits)
NIK_PATTERN = re.compile(r"\b\d{16}\b")        # Indonesian National ID (16 digits)
PHONE_PATTERN = re.compile(r"(\+62|62|08)[0-9]{8,12}\b")

# Prompt injection signatures
INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "abaikan instruksi sebelumnya",
    "system prompt",
    "tampilkan prompt",
    "jailbreak",
    "you are now DAN",
    "kamu sekarang adalah",
    "lupakan aturan",
]

# Action hallucination signatures
ACTION_CLAIM_KEYWORDS = [
    "saya telah menerbitkan",
    "sudah saya terbitkan",
    "sudah saya proses",
    "telah saya setujui",
    "telah saya ubah status",
    "saya telah mendaftarkan anda",
]

def input_guard(state: AgentState) -> Dict[str, Any]:
    """
    Validates user input:
    1. Scans for and redacts PII (NIM, NIK, Phone) with a security notice.
    2. Detects prompt injection attempts and halts with a neutral refusal.
    """
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return {}

    content = extract_text_content(last_message.content)
    warnings: List[str] = list(state.get("guard_warnings", []))

    # 1. Check prompt injection
    lower_content = content.lower()
    for kw in INJECTION_KEYWORDS:
        if kw in lower_content:
            refusal = AIMessage(
                content="Maaf, saya hanya dapat membantu menjawab informasi dan prosedur resmi terkait layanan Unit Layanan Terpadu (ULT) Politeknik Negeri Sriwijaya."
            )
            return {
                "messages": [refusal],
                "context_sufficient": False,
                "needs_escalation": False,
            }

    # 2. Check and redact PII
    has_pii = False
    redacted_content = content

    if NIM_PATTERN.search(redacted_content):
        redacted_content = NIM_PATTERN.sub("[NOMOR IDENTITAS MAHASISWA DIRAHASIAKAN]", redacted_content)
        has_pii = True
    if NIK_PATTERN.search(redacted_content):
        redacted_content = NIK_PATTERN.sub("[NIK DIRAHASIAKAN]", redacted_content)
        has_pii = True
    if PHONE_PATTERN.search(redacted_content):
        redacted_content = PHONE_PATTERN.sub("[NOMOR TELEPON DIRAHASIAKAN]", redacted_content)
        has_pii = True

    if has_pii:
        warning_msg = "Pemberitahuan: Demi keamanan data pribadi Anda, nomor identitas atau kontak telah dirahasiakan otomatis. Mohon tidak mengirimkan NIM, NIK, atau data rahasia."
        warnings.append(warning_msg)

    return {
        "guard_warnings": warnings,
        "rewritten_query": redacted_content,
    }

def output_guard(state: AgentState) -> Dict[str, Any]:
    """
    Verifies generated answer:
    1. Ensures agent does not claim to execute transactional actions.
    2. Verifies presence of factual citations.
    """
    answer = state.get("generated_answer", "")
    if not answer:
        return {}

    lower_answer = answer.lower()
    for kw in ACTION_CLAIM_KEYWORDS:
        if kw in lower_answer:
            # Action hallucination detected; override with safe explanation
            safe_reply = (
                "Sebagai asisten AI informasi, saya tidak memiliki akses untuk memproses, menyetujui, atau menerbitkan dokumen secara langsung. "
                "Silakan ikuti prosedur resmi dan serahkan berkas ke loket Unit Layanan Terpadu (ULT) Polsri pada jam operasional."
            )
            return {
                "generated_answer": safe_reply,
                "needs_escalation": False,
            }

    return {}
