#!/usr/bin/env python3

from **future** import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

try:
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax


RICH_AVAILABLE = True
console = Console()


except ImportError:
RICH_AVAILABLE = False
console = None

SYSTEM_PROMPT = """Tu es OptiPilot-Agent, l'agent d'orchestration exécutif interne de Qualisocial,
entreprise experte en santé mentale et Qualité de Vie au Travail (QVT).

Ton rôle : recevoir une directive brute du responsable (souvent issue d'une note vocale,
donc parfois informelle, orale, non structurée) et la transformer en un paquet exploitable
directement par les équipes Ops, sans jamais trahir l'intention initiale ni sur-interpréter.

Contraintes impératives :

* Si la directive implique des données personnelles, de santé, ou des verbatims de collaborateurs,
  tu dois systématiquement signaler le risque RGPD et imposer une étape d'anonymisation dans le
  cahier des charges technique, AVANT toute analyse.

* Tu ne dois jamais halluciner de contrainte légale ou de fonctionnalité qui ne découle pas
  raisonnablement de la note.

* Ta sortie doit toujours rester factuelle, bienveillante dans le ton de la notification,
  et actionnable.

Tu dois répondre EXCLUSIVEMENT avec un objet JSON strictement valide,
sans aucun texte avant ou après, sans balises markdown.

Respecte EXACTEMENT ce schéma :

{
"meta": {
"agent": "OptiPilot-Agent",
"version": "1.0.0",
"input_source": string,
"processed_at": string,
"provider": string
},
"strategic_analysis": {
"pole_cible": string,
"poles_secondaires_impactes": [string],
"urgence": "Basse" | "Moyenne" | "Haute",
"urgence_justification": string,
"complexite_technique": "Faible" | "Moyenne" | "Élevée",
"complexite_justification": string,
"gain_temps_estime": string,
"risques_identifies": [
{
"type": string,
"niveau": "Faible" | "Moyen" | "Élevé",
"description": string
}
]
},
"cahier_des_charges_technique": {
"objectif": string,
"inputs": [string],
"processing": [string],
"outputs": [string],
"contraintes": [string],
"jalons": [string]
},
"prompt_systeme_genere": string,
"notification": {
"canal": "Slack" | "Email",
"destinataire": string,
"titre": string,
"message_vulgarise": string,
"actions_proposees": [
{
"label": string,
"action_id": string
}
]
}
}

Le champ "prompt_systeme_genere" doit contenir un prompt système COMPLET,
directement utilisable pour un agent LLM chargé d'exécuter concrètement
le besoin décrit par le responsable.

Le champ "message_vulgarise" doit être compréhensible par un non-technique
en moins de 30 secondes de lecture.
"""

def build_user_prompt(raw_note: str, source_label: str) -> str:
return f"""Voici la directive brute à traiter (source: {source_label}) :


## {raw_note.strip()}

Analyse cette directive et produis le JSON attendu, en respectant strictement
le schéma et les contraintes du prompt système."""

def call_groq(raw_note: str, source_label: str = "script") -> str:
from groq import Groq


api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY manquante. "
        "Ajoute-la dans les variables d'environnement de Render."
    )

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model=os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    ),
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
        "type": "json_object",
    },
)

content = response.choices[0].message.content

if not content:
    raise ValueError(
        "Groq a retourné une réponse vide."
    )

return content


def call_mistral(raw_note: str, source_label: str = "script") -> str:
from mistralai import Mistral


api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise ValueError(
        "MISTRAL_API_KEY manquante."
    )

client = Mistral(api_key=api_key)

model = os.getenv(
    "MISTRAL_MODEL",
    "mistral-large-latest",
)

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
    response_format={
        "type": "json_object",
    },
)

content = response.choices[0].message.content

if not content:
    raise ValueError(
        "Mistral a retourné une réponse vide."
    )

return content


def call_demo(raw_note: str, source_label: str = "script") -> str:
base_dir = Path(**file**).resolve().parent


sample_path = (
    base_dir
    / "samples"
    / "output_optipilot_result.json"
)

if not sample_path.exists():
    raise FileNotFoundError(
        "Fichier de démonstration introuvable : "
        f"{sample_path}. "
        "Vérifie que samples/output_optipilot_result.json "
        "est bien présent dans le dépôt GitHub déployé sur Render."
    )

try:
    raw_content = sample_path.read_text(
        encoding="utf-8"
    )

    data = json.loads(raw_content)

except json.JSONDecodeError as exc:
    raise ValueError(
        "Le fichier samples/output_optipilot_result.json "
        f"contient un JSON invalide : {exc}"
    ) from exc

if not isinstance(data, dict):
    raise ValueError(
        "Le fichier de démonstration doit contenir un objet JSON."
    )

if "meta" not in data:
    raise ValueError(
        "Le fichier de démonstration ne contient pas la clé 'meta'."
    )

data["meta"]["processed_at"] = (
    datetime.now(timezone.utc).isoformat()
)

data["meta"]["provider"] = (
    "demo "
    "(rejeu de l'exemple de référence — "
    "aucun appel API effectué)"
)

data["meta"]["input_source"] = source_label

return json.dumps(
    data,
    ensure_ascii=False,
)

PROVIDERS = {
"groq": call_groq,
"mistral": call_mistral,
"demo": call_demo,
}

REQUIRED_TOP_LEVEL_KEYS = {
"meta",
"strategic_analysis",
"cahier_des_charges_technique",
"prompt_systeme_genere",
"notification",
}

def parse_and_validate(raw_response: str) -> dict:
if not isinstance(raw_response, str):
raise ValueError(
"La réponse reçue n'est pas une chaîne JSON."
)

cleaned = raw_response.strip()

if not cleaned:
    raise ValueError(
        "La réponse reçue est vide."
    )

if cleaned.startswith("```"):
    lines = cleaned.splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    cleaned = "\n".join(lines).strip()

try:
    data = json.loads(cleaned)

except json.JSONDecodeError as exc:
    raise ValueError(
        f"Réponse LLM non-JSON ou malformée : {exc}"
    ) from exc

if not isinstance(data, dict):
    raise ValueError(
        "Le JSON retourné doit être un objet."
    )

missing = REQUIRED_TOP_LEVEL_KEYS - set(data.keys())

if missing:
    raise ValueError(
        f"Clés manquantes dans le JSON retourné : {sorted(missing)}"
    )

return data

def display_result(data: dict) -> None:
if not RICH_AVAILABLE:
print(
json.dumps(
data,
indent=2,
ensure_ascii=False,
)
)
return

sa = data["strategic_analysis"]
notif = data["notification"]

console.print(
    Panel.fit(
        f"[bold]Pôle cible :[/bold] "
        f"{sa['pole_cible']}\n"
        f"[bold]Urgence :[/bold] "
        f"{sa['urgence']}   "
        f"[bold]Complexité :[/bold] "
        f"{sa['complexite_technique']}\n"
        f"[bold]Gain de temps estimé :[/bold] "
        f"{sa['gain_temps_estime']}",
        title="📊 Analyse stratégique",
        border_style="cyan",
    )
)

console.print(
    Panel.fit(
        f"[bold]{notif['titre']}[/bold]\n\n"
        f"{notif['message_vulgarise']}\n\n"
        + " | ".join(
            f"[{a['label']}]"
            for a in notif["actions_proposees"]
        ),
        title=(
            f"Notification "
            f"({notif['canal']}) → "
            f"{notif['destinataire']}"
        ),
        border_style="green",
    )
)

console.print(
    Panel(
        Syntax(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            "json",
            theme="monokai",
            word_wrap=True,
        ),
        title="JSON complet",
        border_style="magenta",
    )
)


def run(
input_path: Path,
provider: str,
output_path: Optional[Path] = None,
) -> dict:
if provider not in PROVIDERS:
raise ValueError(
f"Provider inconnu : {provider}. "
f"Providers disponibles : {list(PROVIDERS.keys())}"
)


if not input_path.exists():
    raise FileNotFoundError(
        f"Fichier d'entrée introuvable : {input_path}"
    )

raw_note = input_path.read_text(
    encoding="utf-8"
)

if not raw_note.strip():
    raise ValueError(
        "Le fichier d'entrée est vide."
    )

call_fn = PROVIDERS[provider]

raw_response = call_fn(
    raw_note,
    source_label=input_path.name,
)

data = parse_and_validate(
    raw_response
)

if output_path:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

return data

def main() -> None:
parser = argparse.ArgumentParser(
description=(
"OptiPilot-Agent — transforme une directive "
"brute du responsable en package Ops exploitable."
)
)


parser.add_argument(
    "--input",
    type=Path,
    default=Path(
        "samples/input_note_dg.txt"
    ),
    help=(
        "Chemin vers le fichier texte contenant "
        "la directive brute du responsable."
    ),
)

parser.add_argument(
    "--provider",
    choices=PROVIDERS.keys(),
    default=os.environ.get(
        "OPTIPILOT_PROVIDER",
        "demo",
    ),
    help=(
        "Fournisseur LLM : demo, groq ou mistral."
    ),
)

parser.add_argument(
    "--output",
    type=Path,
    default=None,
    help=(
        "Chemin de sortie pour sauvegarder "
        "le JSON généré."
    ),
)

args = parser.parse_args()

try:
    data = run(
        input_path=args.input,
        provider=args.provider,
        output_path=args.output,
    )

except Exception as exc:
    print(
        f"Erreur de traitement OptiPilot-Agent : "
        f"{type(exc).__name__}: {exc}",
        file=sys.stderr,
    )

    sys.exit(1)

display_result(data)

if args.output:
    print(
        f"\n Résultat sauvegardé dans {args.output}"
    )


if __name__ == "__main__":
    main()
