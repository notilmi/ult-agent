import json
import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.state import AgentState
from src.agent.utils import extract_text_content
from src.config import GEMINI_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

QUERY_REFINE_SYSTEM_PROMPT = """Anda adalah modul pemroses kueri untuk Asisten Unit Layanan Terpadu (ULT) Politeknik Negeri Sriwijaya (Polsri).
Tugas Anda:
1. Analisis riwayat percakapan dan pertanyaan terakhir pengguna.
2. Jika pertanyaan bergantung pada konteks sebelumnya (misal: "bagaimana syaratnya?", "lokasinya di mana?"), ubah menjadi kueri pencarian mandiri (standalone search query) yang jelas dan spesifik terkait layanan Polsri.
3. Klasifikasikan kueri ke dalam salah satu dari 5 kategori resmi:
   - academic: surat keterangan aktif, cuti akademik, pengunduran diri, her-registrasi, nilai/KRS, jadwal akademik.
   - student_affairs: legalisir ijazah/transkrip, beasiswa, asuransi mahasiswa, kegiatan ormawa.
   - general_admin: peminjaman ruangan/fasilitas, surat izin kegiatan, persuratan umum kampus.
   - unit_info: jam buka/operasional ULT, lokasi loket, kontak resmi, struktur layanan.
   - complaints: keluhan, laporan pengaduan, masalah pelayanan, aspirasi.
   - unknown: topik di luar layanan ULT Polsri.
4. Periksa apakah pengguna secara eksplisit meminta berbicara dengan petugas manusia atau staf loket.

Keluarkan respon HANYA dalam format JSON valid:
{
  "rewritten_query": "<kueri mandiri dalam bahasa Indonesia>",
  "category": "<academic|student_affairs|general_admin|unit_info|complaints|unknown>",
  "wants_officer": false
}
"""

def query_refine(state: AgentState) -> Dict[str, Any]:
    """Resolves multi-turn references, categorizes intent, and extracts standalone search query."""
    messages = state.get("messages", [])
    if not messages:
        return {"rewritten_query": "", "category": "unknown", "needs_escalation": False}

    current_query = state.get("rewritten_query")
    if not current_query:
        last_msg = messages[-1]
        current_query = str(last_msg.content)

    # Fast-path check for explicit human officer request
    lower_query = current_query.lower()
    if any(phrase in lower_query for phrase in ["petugas", "manusia", "hubungi staf", "bicara dengan orang"]):
        return {
            "rewritten_query": current_query,
            "category": "unit_info",
            "needs_escalation": True,
        }

    # If complaint, mark category
    if any(phrase in lower_query for phrase in ["lapor", "aduan", "keluhan", "kecewa", "pengaduan"]):
        category = "complaints"
    else:
        category = state.get("category", "unknown")

    try:
        llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.0,
        )

        history_context = []
        for m in messages[:-1][-4:]:  # last 4 messages for context
            role = "Pengguna" if isinstance(m, HumanMessage) else "Asisten"
            history_context.append(f"{role}: {m.content}")

        prompt = (
            f"Riwayat percakapan:\n"
            f"{chr(10).join(history_context) if history_context else 'Belum ada riwayat.'}\n\n"
            f"Pertanyaan pengguna sekarang: {current_query}"
        )

        response = llm.invoke([
            SystemMessage(content=QUERY_REFINE_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        raw_content = extract_text_content(response.content)
        # Clean markdown codeblocks if returned
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
        if raw_content.startswith("```"):
            raw_content = raw_content[3:]
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]

        parsed = json.loads(raw_content.strip())
        rewritten = parsed.get("rewritten_query", current_query)
        detected_category = parsed.get("category", category)
        wants_officer = bool(parsed.get("wants_officer", False))

        return {
            "rewritten_query": rewritten,
            "category": detected_category,
            "needs_escalation": wants_officer or (detected_category == "complaints"),
        }

    except Exception as e:
        logger.warning(f"Query refinement fallback due to error: {e}")
        return {
            "rewritten_query": current_query,
            "category": category or "unknown",
            "needs_escalation": False,
        }
