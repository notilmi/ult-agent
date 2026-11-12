import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.state import AgentState
from src.agent.utils import extract_text_content
from src.config import GEMINI_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Anda adalah "Asisten ULT Polsri", asisten resmi Unit Layanan Terpadu Politeknik Negeri Sriwijaya (Polsri).
Peran Anda adalah memberikan informasi prosedur, persyaratan, dan alur layanan resmi kepada mahasiswa, dosen, dan staf Polsri.

ATURAN UTAMA:
1. JAWAB HANYA berdasarkan konteks dokumen resmi yang diberikan. JANGAN PERNAH mengarang, berasumsi, atau menambahkan syarat/tanggal/jam/link yang tidak tertulis pada konteks.
2. Gunakan Bahasa Indonesia baku yang formal namun ramah, dengan sapaan "Anda".
3. Struktur jawaban jika menjelaskan prosedur:
   - Persyaratan (gunakan poin-poin)
   - Alur / Tahapan Pengajuan
   - Unit yang Bertanggung Jawab
   - Tautan Formulir Resmi (jika ada pada dokumen)
4. Pada akhir jawaban, WAJIB mencantumkan rujukan sumber resmi:
   Contoh: "[Sumber: SOP Pelayanan Administrasi Akademik 2025 | Terverifikasi: 2026-10-15]"
5. JANGAN PERNAH meminta NIM, NIK, password, atau dokumen pribadi pengguna.
6. JANGAN PERNAH menyatakan bahwa Anda telah memproses, menerbitkan, atau menyetujui dokumen secara langsung. Anda adalah asisten informasi.
"""

def generate_answer(state: AgentState) -> Dict[str, Any]:
    """Generates a strictly grounded response using Gemini 3.8 Flash based on retrieved context."""
    query = state.get("rewritten_query", "")
    docs = state.get("retrieved_documents", [])
    warnings = state.get("guard_warnings", [])

    if not docs:
        return {
            "generated_answer": "Maaf, informasi mengenai layanan tersebut belum tersedia pada basis data kami.",
            "citations": [],
        }

    # Format retrieved passages into prompt context
    context_blocks = []
    citations: List[str] = []

    for i, doc in enumerate(docs):
        entry_id = doc.get("entry_id", "FAQ")
        source = doc.get("source_title", "Dokumen ULT")
        verified = doc.get("verified_at", "-")
        citation_str = f"{source} ({entry_id})"
        if citation_str not in citations:
            citations.append(citation_str)

        block = (
            f"[Dokumen {i+1}: {doc.get('source_title')} | Kategori: {doc.get('category')} | Verifikasi: {verified}]\n"
            f"{doc.get('content')}\n"
        )
        if doc.get("form_url"):
            block += f"Tautan Formulir: {doc.get('form_url')}\n"
        if doc.get("responsible_unit"):
            block += f"Unit Penanggung Jawab: {doc.get('responsible_unit')}\n"

        context_blocks.append(block)

    context_str = "\n---\n".join(context_blocks)

    user_prompt = (
        f"Konteks Dokumen Resmi ULT Polsri:\n{context_str}\n\n"
        f"Pertanyaan Pengguna: {query}\n\n"
        f"Berikan jawaban yang jelas, terstruktur, dan bersumber langsung dari konteks di atas."
    )

    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.1,
    )

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        answer_text = extract_text_content(response.content)

        # Prepend PII safety warning if any was flagged by input guard
        if warnings:
            prefix = "\n\n> ⚠️ *" + "\n> ⚠️ *".join(warnings) + "*\n\n"
            answer_text = prefix + answer_text

        ai_message = AIMessage(content=answer_text)

        return {
            "messages": [ai_message],
            "generated_answer": answer_text,
            "citations": citations,
            "fallback_count": 0,  # Reset fallback counter on successful resolution
        }

    except Exception as e:
        logger.error(f"Error in Gemini 3.8 Flash generation: {e}")
        fallback_msg = AIMessage(
            content="Mohon maaf, terjadi kendala saat menghubungkan ke sistem pemrosesan jawaban. Silakan coba kembali sesaat lagi atau hubungi petugas ULT."
        )
        return {
            "messages": [fallback_msg],
            "generated_answer": fallback_msg.content,
            "citations": [],
            "needs_escalation": True,
        }
