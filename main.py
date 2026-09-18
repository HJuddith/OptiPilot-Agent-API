import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

MAX_INPUT_BYTES = 50_000
LLM_TIMEOUT_SECONDS = 60


REQUIRED_TOP_LEVEL_KEYS = {
    "meta",
    "strategic_analysis",
    "cahier_des_charges_technique",
    "prompt_systeme_genere",
    "notification",
}


# ============================================================
# PROMPT
# ============================================================

def load_system_prompt() -> str:
    prompt_path = BASE_DIR / "prompts" / "system_prompt.txt"

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt introuvable : {prompt_path}"
        )

    prompt = prompt_path.read_text(
        encoding="utf-8"
    ).strip()

    if not prompt:
        raise ValueError(
            f"Le fichier de prompt est vide : {prompt_path}"
        )

    return prompt


SYSTEM_PROMPT = load_system_prompt()


# ============================================================
# UTILITAIRES
# ============================================================

def read_input_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {path}"
        )

    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(
            f"Fichier trop volumineux : {path}"
        )

    content = path.read_text(
        encoding="utf-8"
    ).strip()

    if not content:
        raise ValueError(
            f"Le fichier est vide : {path}"
        )

    return content


def get_api_key(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"La variable d'environnement {name} est absente."
        )

    return value


# ============================================================
# PROMPT UTILISATEUR
# ============================================================

def build_user_prompt(
    raw_note: str,
    source_label: str,
) -> str:

    return (
        f"Voici la directive brute à traiter "
        f"(source : {source_label}) :\n\n"
        f"{raw_note.strip()}\n\n"
        "Analyse cette directive et produis le JSON attendu, "
        "en respectant strictement le schéma et les contraintes "
        "du prompt système."
    )


# ============================================================
# GROQ
# ============================================================

def call_groq(
    raw_note: str,
    source_label: str = "script",
) -> str:

    from groq import Groq

    client = Groq(
        api_key=get_api_key("GROQ_API_KEY")
    )

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-120b",
    ).strip()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_user_prompt(
                    raw_note,
                    source_label,
                ),
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_object"
        },
        timeout=LLM_TIMEOUT_SECONDS,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Groq a retourné une réponse vide."
        )

    return content


# ============================================================
# MISTRAL
# ============================================================

def call_mistral(
    raw_note: str,
    source_label: str = "script",
) -> str:

    from mistralai import Mistral

    client = Mistral(
        api_key=get_api_key("MISTRAL_API_KEY")
    )

    model = os.getenv(
        "MISTRAL_MODEL",
        "mistral-small-latest",
    ).strip()

    response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_user_prompt(
                    raw_note,
                    source_label,
                ),
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Mistral a retourné une réponse vide."
        )

    return content


# ============================================================
# DEMO
# ============================================================

def call_demo(
    raw_note: str,
    source_label: str = "script",
) -> str:

    sample_path = (
        BASE_DIR
        / "samples"
        / "output_optipilot_result.json"
    )

    raw_content = read_input_file(
        sample_path
    )

    data = json.loads(raw_content)

    data["meta"]["processed_at"] = (
        datetime.now(timezone.utc).isoformat()
    )

    data["meta"]["provider"] = (
        "demo "
        "(rejeu de l'exemple de référence - "
        "aucun appel API effectué)"
    )

    data["meta"]["input_source"] = source_label

    return json.dumps(
        data,
        ensure_ascii=False,
    )


# ============================================================
# PROVIDERS
# ============================================================

PROVIDERS = {
    "groq": call_groq,
    "mistral": call_mistral,
    "demo": call_demo,
}


# ============================================================
# TRAITEMENT
# ============================================================

def process(
    raw_note: str,
    provider_name: str,
    source_label: str,
) -> dict:

    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Provider inconnu : {provider_name}"
        )

    provider = PROVIDERS[provider_name]

    raw_result = provider(
        raw_note,
        source_label,
    )

    from utils.validators import extract_json_object

    return extract_json_object(
        raw_result
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description="OptiPilot-Agent"
    )

    parser.add_argument(
        "--input",
        default="samples/input_note_resp.txt",
        help="Chemin vers la directive brute",
    )

    parser.add_argument(
        "--provider",
        choices=PROVIDERS.keys(),
        default="groq",
        help="Provider LLM",
    )

    parser.add_argument(
        "--output",
        help="Fichier JSON de sortie optionnel",
    )

    args = parser.parse_args()

    input_path = BASE_DIR / args.input

    raw_note = read_input_file(
        input_path
    )

    result = process(
        raw_note=raw_note,
        provider_name=args.provider,
        source_label=input_path.name,
    )

    output_json = json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    )

    if args.output:
        output_path = BASE_DIR / args.output

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            output_json,
            encoding="utf-8",
        )

        print(
            f"Résultat enregistré dans : "
            f"{output_path}"
        )
    else:
        print(output_json)


if __name__ == "__main__":
    main()

