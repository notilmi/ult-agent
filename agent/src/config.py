import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from agent root directory
AGENT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(AGENT_ROOT / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")

# Models
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.8-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")

# Retrieval & Guard Thresholds
SIMILARITY_SCORE_THRESHOLD = float(os.getenv("SIMILARITY_SCORE_THRESHOLD", "0.55"))
TOP_K_DOCUMENTS = int(os.getenv("TOP_K_DOCUMENTS", "4"))
MAX_FALLBACK_COUNT = int(os.getenv("MAX_FALLBACK_COUNT", "2"))

# Service Metadata (Polsri ULT)
ULT_OFFICE_HOURS = """Senin - Kamis: 08.00 - 15.00 WIB (Istirahat 12.00 - 13.00 WIB)
Jumat: 08.00 - 15.30 WIB (Istirahat 11.30 - 13.30 WIB)
Sabtu & Minggu: Tutup"""

ULT_LOCATION = "Gedung Kantor Pusat Administrasi Polsri, Lantai 1 (Sayap Kanan), Bukit Besar, Palembang"
ULT_EMAIL = "ult@polsri.ac.id"
ULT_WHATSAPP = "+62 812-7890-1234"
ULT_HELPDESK_URL = "https://helpdesk.polsri.ac.id"
ULT_COMPLAINTS_URL = "https://lapor.polsri.ac.id"
