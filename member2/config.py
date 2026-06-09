"""Central configuration. Reads from environment variables with sensible defaults."""
import os
from pathlib import Path

# --- LLM provider ---
LLM_PROVIDER    = "gemini"
LLM_MODEL       = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_MAX_TOKENS  = int(os.getenv("LLM_MAX_TOKENS", "2048"))
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")

# --- Rate limiting ---
GEMINI_RPM      = 60   # paid tier allows up to 1000 RPM; use 60 to be safe
GEMINI_FREE_RPM = 9    # kept for reference
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROQ_FREE_RPM   = int(os.getenv("GROQ_FREE_RPM", "6"))
RETRY_MAX_ATTEMPTS = 5
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
