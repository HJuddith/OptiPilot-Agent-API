from pathlib import Path

from utils.config import PROMPT_PATH


def load_system_prompt() -> str:
    """
    Charge le prompt système depuis le fichier texte.
    """

    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt introuvable : {PROMPT_PATH}"
        )

    prompt = PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()

    if not prompt:
        raise ValueError(
            f"Le fichier de prompt est vide : {PROMPT_PATH}"
        )

    return prompt
