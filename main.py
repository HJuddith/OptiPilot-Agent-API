#!/usr/bin/env python3
"""
OptiPilot-Agent — Agent d'orchestration exécutif pour Qualisocial.

Transforme une directive brute du DG (texte / transcription de note vocale) en :
  1. Une analyse stratégique (pôle cible, urgence, complexité, gain de temps)
  2. Un cahier des charges technique pour les Ops
  3. Un prompt système optimisé, prêt à être injecté dans un agent d'exécution
  4. Une notification Slack/Email vulgarisée avec des actions proposées

Usage:
    python main.py --input samples/input_note_dg.txt --provider demo
    python main.py --input samples/input_note_dg.txt --provider groq
    python main.py --input samples/input_note_dg.txt --provider mistral --output out.json

Auteur: Projet portfolio — candidature Tech Ops / AI Builder, Qualisocial.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from groq import Groq
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
    console = Console()
except ImportError:  # rich est optionnel, le script doit rester exécutable sans
    RICH_AVAILABLE = False
    console = None


#----------------------------------------------------------------
# 1. PROMPT SYSTÈME — cœur de l'agent OptiPilot
#---------------------------------------------------------------

SYSTEM_PROMPT = """Tu es OptiPilot-Agent, l'agent d'orchestration exécutif interne de Qualisocial,
entreprise experte en santé mentale et Qualité de Vie au Travail (QVT).

Ton rôle : recevoir une directive brute du Directeur Général (souvent issue d'une note vocale,
donc parfois informelle, orale, non structurée) et la transformer en un paquet exploitable
directement par les équipes Ops, sans jamais trahir l'intention initiale ni sur-interpréter.

Contraintes impératives (Qualisocial est une entreprise de santé mentale/QVT — la rigueur sur
les données sensibles n'est jamais optionnelle) :
- Si la directive implique des données personnelles, de santé, ou des verbatims de collaborateurs,
  tu dois systématiquement signaler le risque RGPD et imposer une étape d'anonymisation dans le
  cahier des charges technique, AVANT toute analyse.
- Tu ne dois jamais halluciner de contrainte légale ou de fonctionnalité qui ne découle pas
  raisonnablement de la note.
- Ta sortie doit toujours rester factuelle, bienveillante dans le ton de la notification (le DG
  et les équipes travaillent dans un contexte de santé mentale — le ton compte), et actionnable.

Tu dois répondre EXCLUSIVEMENT avec un objet JSON strictement valide, sans aucun texte avant ou
après, sans balises markdown, respectant EXACTEMENT ce schéma :

{
  "meta": {
    "agent": "OptiPilot-Agent",
    "version": "1.0.0",
    "input_source": string,
    "processed_at": string (ISO 8601),
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
      { "type": string, "niveau": "Faible" | "Moyen" | "Élevé", "description": string }
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
    "actions_proposees": [ { "label": string, "action_id": string } ]
  }
}

Le champ "prompt_systeme_genere" doit contenir un prompt système COMPLET, directement utilisable,
pour un agent LLM chargé d'exécuter concrètement le besoin décrit par le DG.

Le champ "message_vulgarise" doit être compréhensible par un non-technique en moins de 30 secondes
de lecture, sans jargon.
"""


def build_user_prompt(raw_note: str, source_label: str) -> str:
    """Construit le message utilisateur envoyé au LLM à partir de la note brute du DG."""
    return f"""Voici la directive brute à traiter (source: {source_label}) :

---
{raw_note.strip()}
---

Analyse cette directive et produis le JSON attendu, en respectant strictement le schéma et les
contraintes du prompt système."""


# --------------------------------------------------------------------------- #
# 2. APPELS LLM — Groq (par défaut), Mistral (fallback souverain), Demo
# --------------------------------------------------------------------------- #

import os
from groq import Groq

def call_groq(raw_note: str, source_label: str = "script") -> str:
    """Appel à l'API gratuite de Groq (Llama 3.3 70B)"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY manquante dans le fichier .env")

    client = Groq(api_key=api_key)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(raw_note, source_label)}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}  # Force le format JSON strict
    )
    
    return response.choices[0].message.content


def call_mistral(raw_note: str, source_label: str) -> str:
    """Appelle l'API Mistral (fallback souverain / hébergement UE) et renvoie le JSON brut."""
    from mistralai import Mistral

    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    model = os.environ.get("MISTRAL_MODEL", "mistral-large-latest")

    response = client.chat.complete(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(raw_note, source_label)},
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def call_demo(raw_note: str, source_label: str) -> str:
    """
    Mode démo : ne fait aucun appel API. Permet à un recruteur ou tout évaluateur d'exécuter
    le projet sans clé, en rejouant l'exemple de référence stocké dans samples/.
    Utile aussi comme "golden output" pour les tests de non-régression du parsing JSON.
    """
    sample_path = Path(__file__).parent / "samples" / "output_optipilot_result.json"
    data = json.loads(sample_path.read_text(encoding="utf-8"))
    data["meta"]["processed_at"] = datetime.now(timezone.utc).isoformat()
    data["meta"]["provider"] = "demo (rejeu de l'exemple de référence — aucun appel API effectué)"
    return json.dumps(data, ensure_ascii=False)


PROVIDERS = {
    "groq": call_groq,
    "mistral": call_mistral,
    "demo": call_demo,
}


# --------------------------------------------------------------------------- #
# 3. PARSING & VALIDATION
# --------------------------------------------------------------------------- #

REQUIRED_TOP_LEVEL_KEYS = {
    "meta",
    "strategic_analysis",
    "cahier_des_charges_technique",
    "prompt_systeme_genere",
    "notification",
}


def parse_and_validate(raw_response: str) -> dict:
    """Parse la réponse du LLM en JSON strict et valide la présence des clés attendues."""
    cleaned = raw_response.strip()
    # Filet de sécurité si un modèle renvoie malgré tout des balises markdown ```json ... ```
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Réponse LLM non-JSON ou malformée : {exc}") from exc

    missing = REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        raise ValueError(f"Clés manquantes dans le JSON retourné : {missing}")

    return data


# --------------------------------------------------------------------------- #
# 4. AFFICHAGE CONSOLE (pédagogique — pense aux profils non-tech qui liront le README)
# --------------------------------------------------------------------------- #

def display_result(data: dict) -> None:
    """Affiche un résumé lisible du résultat dans le terminal."""
    if not RICH_AVAILABLE:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    sa = data["strategic_analysis"]
    notif = data["notification"]

    console.print(Panel.fit(
        f"[bold]Pôle cible :[/bold] {sa['pole_cible']}\n"
        f"[bold]Urgence :[/bold] {sa['urgence']}   "
        f"[bold]Complexité :[/bold] {sa['complexite_technique']}\n"
        f"[bold]Gain de temps estimé :[/bold] {sa['gain_temps_estime']}",
        title="📊 Analyse stratégique", border_style="cyan",
    ))

    console.print(Panel.fit(
        f"[bold]{notif['titre']}[/bold]\n\n{notif['message_vulgarise']}\n\n"
        + " | ".join(f"[{a['label']}]" for a in notif["actions_proposees"]),
        title=f"📩 Notification ({notif['canal']}) → {notif['destinataire']}",
        border_style="green",
    ))

    console.print(Panel(
        Syntax(json.dumps(data, indent=2, ensure_ascii=False), "json", theme="monokai",
               word_wrap=True),
        title="🧾 JSON complet (contrat d'interface Make/n8n)", border_style="magenta",
    ))


# --------------------------------------------------------------------------- #
# 5. POINT D'ENTRÉE CLI
# --------------------------------------------------------------------------- #

def run(input_path: Path, provider: str, output_path: Optional[Path]) -> dict:
    raw_note = input_path.read_text(encoding="utf-8")
    call_fn = PROVIDERS[provider]

    raw_response = call_fn(raw_note, source_label=input_path.name)
    data = parse_and_validate(raw_response)

    if output_path:
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    return data


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="OptiPilot-Agent — transforme une directive brute du DG en package Ops exploitable."
    )
    parser.add_argument("--input", type=Path, default=Path("samples/input_note_dg.txt"),
                         help="Chemin vers le fichier texte contenant la note brute du DG.")
    parser.add_argument("--provider", choices=PROVIDERS.keys(),
                         default=os.environ.get("OPTIPILOT_PROVIDER", "demo"),
                         help="Fournisseur LLM à utiliser (defaut: demo, aucune clé requise).")
    parser.add_argument("--output", type=Path, default=None,
                         help="Chemin de sortie pour sauvegarder le JSON généré.")
    args = parser.parse_args()

    if not args.input.exists():
        print(f" Fichier d'entrée introuvable : {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        data = run(args.input, args.provider, args.output)
    except (ValueError, KeyError) as exc:
        print(f" Erreur de traitement OptiPilot-Agent : {exc}", file=sys.stderr)
        sys.exit(1)

    display_result(data)

    if args.output:
        print(f"\n Résultat sauvegardé dans {args.output}")


if __name__ == "__main__":
    main()
