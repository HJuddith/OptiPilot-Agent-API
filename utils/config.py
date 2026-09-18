import os
from pathlib import Path


# ============================================================
# CHEMINS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROMPT_PATH = (
    BASE_DIR
    / "prompts"
    / "system_prompt.txt"
)

SAMPLES_DIR = (
    BASE_DIR
    / "samples"
)


# ============================================================
# LIMITES
# ============================================================

MAX_INPUT_BYTES = 50_000

LLM_TIMEOUT_SECONDS = 60


# ============================================================
# MODÈLES
# ============================================================

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
).strip()

MISTRAL_MODEL = os.getenv(
    "MISTRAL_MODEL",
    "mistral-small-latest",
).strip()


# ============================================================
# PROVIDERS
# ============================================================

SUPPORTED_PROVIDERS = {
    "groq",
    "mistral",
    "demo",
}


# ============================================================
# CLÉS API
# ============================================================

def get_api_key(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"La variable d'environnement {name} est absente."
        )

    return value

