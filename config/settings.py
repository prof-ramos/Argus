import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.getenv("ARGUS_OUTPUT_DIR", BASE_DIR / "reports"))
OUTPUT_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

COLLECTOR_TIMEOUT = int(os.getenv("COLLECTOR_TIMEOUT", "30"))
MAIGRET_TOP_SITES = int(os.getenv("MAIGRET_TOP_SITES", "20"))
VALIDATE_URLS = os.getenv("VALIDATE_URLS", "true").lower() == "true"
VALIDATION_TIMEOUT = int(os.getenv("VALIDATION_TIMEOUT", "5"))

FALSE_POSITIVE_SITES = [
    "example.com",
    "test.com",
]
