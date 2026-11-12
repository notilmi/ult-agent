from typing import Dict, Any
from langchain_core.messages import AIMessage
from src.agent.state import AgentState
from src.config import (
    ULT_OFFICE_HOURS,
    ULT_LOCATION,
    ULT_EMAIL,
    ULT_WHATSAPP,
    ULT_HELPDESK_URL,
    ULT_COMPLAINTS_URL,
    MAX_FALLBACK_COUNT,
)

def fallback(state: AgentState) -> Dict[str, Any]:
    """
    Handles cases where information is not found in the validated knowledge base.
    Increments fallback_count and offers rephrasing or officer escalation.
    """
    current_fallbacks = state.get("fallback_count", 0) + 1

    if current_fallbacks >= MAX_FALLBACK_COUNT:
        # Trigger officer escalation after repeated fallback
        return {
            "fallback_count": current_fallbacks,
            "needs_escalation": True,
        }

    message_text = (
        "Mohon maaf, informasi mengenai hal tersebut belum tersedia atau belum terverifikasi pada basis pengetahuan resmi ULT Polsri.\n\n"
        "Silakan coba tanyakan kembali dengan kata kunci yang lebih spesifik, atau Anda dapat memilih untuk langsung menghubungi petugas layanan kami."
    )

    return {
        "messages": [AIMessage(content=message_text)],
        "generated_answer": message_text,
        "fallback_count": current_fallbacks,
        "needs_escalation": False,
    }

def escalate(state: AgentState) -> Dict[str, Any]:
    """
    Provides official contact channels, operating hours, and location for human officer escalation.
    """
    is_complaint = state.get("category") == "complaints"

    if is_complaint:
        escalation_text = (
            "### Layanan Pengaduan & Aspirasi ULT Polsri\n\n"
            "Untuk menyampaikan pengaduan resmi, keluhan pelayanan, atau aspirasi, Anda dapat menggunakan saluran resmi berikut:\n\n"
            f"1. **Portal Pengaduan Online**: [{ULT_COMPLAINTS_URL}]({ULT_COMPLAINTS_URL})\n"
            f"2. **Loket Meja Pengaduan Langsung**: {ULT_LOCATION}\n"
            f"3. **Email**: {ULT_EMAIL}\n\n"
            f"**Jam Layanan Tatap Muka:**\n{ULT_OFFICE_HOURS}\n\n"
            "*Petugas ULT dan Satuan Pengawas Internal (SPI) akan memverifikasi dan menindaklanjuti laporan Anda secara tertutup dan aman.*"
        )
    else:
        escalation_text = (
            "### Bantuan Petugas Layanan ULT Polsri\n\n"
            "Untuk bantuan langsung atau pengurusan dokumen yang memerlukan verifikasi petugas, silakan hubungi kanal resmi berikut:\n\n"
            f"- **Lokasi Pelayanan**: {ULT_LOCATION}\n"
            f"- **Jam Operasional**:\n{ULT_OFFICE_HOURS}\n"
            f"- **WhatsApp Informasi**: {ULT_WHATSAPP} *(pesan teks jam kerja)*\n"
            f"- **Email**: [{ULT_EMAIL}](mailto:{ULT_EMAIL})\n"
            f"- **Helpdesk Online**: [{ULT_HELPDESK_URL}]({ULT_HELPDESK_URL})\n\n"
            "Petugas loket ULT siap membantu Anda pada jam operasional."
        )

    return {
        "messages": [AIMessage(content=escalation_text)],
        "generated_answer": escalation_text,
        "fallback_count": 0,
        "needs_escalation": False,
    }
