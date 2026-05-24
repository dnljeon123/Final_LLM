"""Central configuration. Reads from environment variables with sensible defaults."""
import os
from pathlib import Path

# --- LLM provider ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "400"))

# --- Rate limiting ---
GEMINI_FREE_RPM = 15  # Free tier limit
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 2.0  # seconds

# --- Paths ---
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
CACHE_DIR = ROOT / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# --- Evaluation ---
TEST_SPLIT_SEED = 42
TEST_SPLIT_RATIO = 0.2
EVAL_REPEATS = 3

# --- UI ---
GRADIO_PORT = int(os.getenv("GRADIO_PORT", "7860"))
GRADIO_SHARE = os.getenv("GRADIO_SHARE", "false").lower() == "true"


def require_api_key() -> str:
    """Raise a clear error if the API key is missing."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Get a free key at "
            "https://aistudio.google.com/apikey and export it as an env var."
        )
    return GEMINI_API_KEY
