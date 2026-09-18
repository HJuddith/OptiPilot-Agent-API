#!/usr/bin/env python3
"""OptiPilot-Agent - transforme une directive brute en package Ops exploitable."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from dotenv import load_dotenv

load_dotenv()

# ---------- Console (optionnelle) ----------
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax

    console: Optional[Console] = Console()
except ImportError:
    console = None


# ---------- Constantes ----------
MAX_INPUT_BYTES = 200_000
MAX_OUTPUT_BYTES = 5_000_000
LLM_TIMEOUT_SECONDS = 60.0

REQUIRED_TOP_LEVEL_KEYS = {
    "meta",
    "strategic_analysis",
    "cahier_des_charges_technique",
    "prompt_systeme_genere",
    "notification",
}


# ---------- Actions Slack ----------
DEFAULT_QVT_ACTIONS = [
    {
        "label": "Valider pour le Codex",
        "action_id": "validate_codex",
    },
    {
        "label": "Demander relecture RH",
        "action_id": "request_rh_review",
    },
    {
        "label": "Reporter",
        "action_id": "postpone",
    },
]

CLARIFICATION_ACTIONS = [
    {
        "label": "Demander clarification",
        "action_id": "request_clarification",
    },
    {
        "label": "Reporter",
        "action_id": "postpone",
    },
    {
        "label": "Annuler",
        "action_id": "cancel",
    },
]


# ---------- Prompt système ----------
SYSTEM_PROMPT = """Tu es OptiPilot-Agent, l'agent d'orchestration executive interne d'une entreprise experte en sante mentale et Qualite de Vie au Travail (QVT).

Ton role : recevoir une directive brute du responsable et la transformer en paquet exploitable directement par les equipes Ops, sans jamais trahir l'intention initiale ni sur-interpreter.

Contraintes imperatives :
- Si la directive implique des donnees personnelles, de sante, ou des verbatims de collaborateurs, tu dois systematiquement signaler le risque RGPD et imposer une etape d'anonymisation dans le cahier des charges technique, AVANT toute analyse.
- Tu ne dois jamais halluciner de contrainte legale ou de fonctionnalite qui ne decoule pas raisonnablement de la note.
- Ta sortie doit toujours rester factuelle, bienveillante dans le ton de la notification, et actionnable.

REGLE ABSOLUE SUR LES NOMS PROPRES (conformite RGPD) :
- Tu ne dois JAMAIS citer de nom propre (prenom, nom de famille, initiales) dans AUCUN champ de ta sortie JSON.
- Le champ "notification.destinataire" doit contenir uniquement un canal ou un role, jamais un nom de personne.
- Exemples valides : "#qvt-direction", "Equipe RH", "Direction Generale", "#optipilot-alerts".
- Exemples interdits : "Jean Bernard (PDG)", "M. Dupont", "Sophie".
- Si la directive contient un nom de personne, remplace-le par un role generique.

REGLE SUR LE MESSAGE :
- "notification.message_vulgarise" doit commencer par une formule neutre.
- Le message doit etre comprehensible par un non-technique en moins de 30 secondes.
- Le message doit contenir un saut de ligne apres la formule d'ouverture.
- Le message doit se terminer par une formule de cloture bienveillante et inclusive.
- La cloture doit s'adresser a un collectif.
- Exemples : "Bonne continuation a tous.", "Excellente journee a tous.", "Bonne journee a toutes et a tous.", "Bien a vous."

REGLE OBLIGATOIRE SUR LES ACTIONS :
- "notification.actions_proposees" doit toujours contenir EXACTEMENT 3 objets.
- Chaque objet doit obligatoirement contenir un "label" non vide.
- Chaque objet doit obligatoirement contenir un "action_id" non vide.
- Ne retourne JAMAIS 0, 1 ou 2 actions.
- Pour une directive exploitable, utilise exactement ces trois actions :

1. {"label": "Valider pour le Codex", "action_id": "validate_codex"}
2. {"label": "Demander relecture RH", "action_id": "request_rh_review"}
3. {"label": "Reporter", "action_id": "postpone"}

- Si la directive necessite une clarification, utilise exactement ces trois actions :

1. {"label": "Demander clarification", "action_id": "request_clarification"}
2. {"label": "Reporter", "action_id": "postpone"}
3. {"label": "Annuler", "action_id": "cancel"}

- Les actions doivent toujours etre presentes meme lorsqu'une clarification est necessaire.

Tu dois repondre EXCLUSIVEMENT avec un objet JSON strictement valide, sans aucun texte avant ou apres, sans balises markdown.

Respecte EXACTEMENT ce schema :

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
    "complexite_technique": "Faible" | "Moyenne" | "Elevee",
    "complexite_justification": string,
    "gain_temps_estime": string,
    "risques_identifies": [
      {
        "type": string,
        "niveau": "Faible" | "Moyen" | "Eleve",
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
      },
      {
        "label": string,
        "action_id": string
      },
      {
        "label": string,
        "action_id": string
      }
    ]
  }
}

Le champ "prompt_systeme_genere" doit contenir un prompt systeme COMPLET, directement utilisable pour un agent LLM charge d'executer concretement le besoin decrit par le responsable.

Le champ "message_vulgarise" doit etre comprehensible par un non-technique en moins de 30 secondes de lecture et se terminer par une formule de cloture bienveillante adressee a un collectif."""


# ---------- Helpers ----------
def build_user_prompt(raw_note: str, source_label: str) -> str:
    return (
        f"Voici la directive brute a traiter (source: {source_label}) :\n\n"
        f"{raw_note.strip()}\n\n"
        "Analyse cette directive et produis le JSON attendu. "
        "Respecte strictement le schema, les contraintes RGPD, "
        "et la regle imposant exactement 3 actions dans notification.actions_proposees."
    )


def _safe_read_text(path: Path, max_bytes: int) -> str:
    """Lit un fichier avec une limite de taille."""
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    if not path.is_file():
        raise ValueError(f"Ce n'est pas un fichier regulier : {path}")

    size = path.stat().st_size

    if size > max_bytes:
        raise ValueError(
            f"Fichier trop volumineux ({size} octets > {max_bytes} autorises)."
        )

    return path.read_text(encoding="utf-8")


def _get_api_key(env_var: str) -> str:
    """Recupere une cle API sans jamais la logger."""
    key = os.getenv(env_var)

    if not key or not key.strip():
        raise ValueError(
            f"Variable d'environnement {env_var} manquante ou vide. "
            f"Configurez-la dans Render (Environment Variables)."
        )

    return key.strip()


def _normalize_actions(notification: dict) -> None:
    """
    Garantit que Slack recevra toujours exactement 3 actions valides.
    """

    actions = notification.get("actions_proposees")

    if not isinstance(actions, list):
        actions = []

    # Nettoyage des actions existantes
    valid_actions = []

    for action in actions:
        if not isinstance(action, dict):
            continue

        label = str(action.get("label", "")).strip()
        action_id = str(action.get("action_id", "")).strip()

        if label and action_id:
            valid_actions.append(
                {
                    "label": label,
                    "action_id": action_id,
                }
            )

    # Détection d'une demande de clarification
    clarification = any(
        action.get("action_id") == "request_clarification"
        for action in valid_actions
    )

    if clarification:
        notification["actions_proposees"] = CLARIFICATION_ACTIONS.copy()
        return

    # Pour une directive exploitable, on impose les trois actions QVT.
    notification["actions_proposees"] = DEFAULT_QVT_ACTIONS.copy()


def _extract_json_object(raw: str) -> dict:
    """Extrait et valide le premier objet JSON valide d'une reponse LLM."""

    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Reponse LLM vide ou non textuelle.")

    cleaned = raw.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    try:
        data = json.loads(cleaned)

    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                "Aucun objet JSON detecte dans la reponse LLM."
            )

        try:
            data = json.loads(cleaned[start:end + 1])

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"JSON LLM malforme : {exc}"
            ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "Le JSON retourne doit etre un objet."
        )

    missing = REQUIRED_TOP_LEVEL_KEYS - data.keys()

    if missing:
        raise ValueError(
            f"Cles manquantes dans le JSON : {sorted(missing)}"
        )

    notification = data.get("notification")

    if not isinstance(notification, dict):
        raise ValueError(
            "Le champ 'notification' doit etre un objet JSON."
        )

    # Correction automatique des actions avant envoi vers Make/Slack.
    _normalize_actions(notification)

    return data


# Alias public pour l'API
extract_json_object = _extract_json_object


# ---------- Providers ----------
def call_groq(
    raw_note: str,
    source_label: str = "script",
) -> str:

    try:
        from groq import Groq

    except ImportError as exc:
        raise RuntimeError(
            "Package 'groq' non installe. "
            "Ajoutez-le dans requirements.txt."
        ) from exc

    client = Groq(
        api_key=_get_api_key("GROQ_API_KEY")
    )

    model = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
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
            "Groq a retourne une reponse vide."
        )

    return content


def call_mistral(
    raw_note: str,
    source_label: str = "script",
) -> str:

    try:
        from mistralai import Mistral

    except ImportError as exc:
        raise RuntimeError(
            "Package 'mistralai' non installe. "
            "Ajoutez-le dans requirements.txt."
        ) from exc

    client = Mistral(
        api_key=_get_api_key("MISTRAL_API_KEY")
    )

    model = os.getenv(
        "MISTRAL_MODEL",
        "mistral-large-latest",
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
            "Mistral a retourne une reponse vide."
        )

    return content


def call_demo(
    raw_note: str,
    source_label: str = "script",
) -> str:
    """Rejoue un exemple fige sans appel API."""

    base_dir = Path(__file__).resolve().parent

    sample_path = (
        base_dir
        / "samples"
        / "output_optipilot_result.json"
    )

    raw_content = _safe_read_text(
        sample_path,
        MAX_INPUT_BYTES,
    )

    try:
        data = json.loads(raw_content)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Le fichier de demonstration contient "
            f"un JSON invalide : {exc}"
        ) from exc

    if not isinstance(data, dict) or "meta" not in data:
        raise ValueError(
            "Le fichier de demo doit etre un objet JSON "
            "avec 'meta'."
        )

    data["meta"]["processed_at"] = (
        datetime.now(timezone.utc).isoformat()
    )

    data["meta"]["provider"] = (
        "demo "
        "(rejeu de l'exemple de reference - "
        "aucun appel API effectue)"
    )

    data["meta"]["input_source"] = source_label

    return json.dumps(
        data,
        ensure_ascii=False,
    )


PROVIDERS: dict[str, Callable[[str, str], str]] = {
    "groq": call_groq,
    "mistral": call_mistral,
    "demo": call_demo,
}


# ---------- Affichage ----------
def display_result(data: dict) -> None:

    if console is None:
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
            f"[bold]Pole cible :[/bold] "
            f"{sa['pole_cible']}\n"
            f"[bold]Urgence :[/bold] "
            f"{sa['urgence']}   "
            f"[bold]Complexite :[/bold] "
            f"{sa['complexite_technique']}\n"
            f"[bold]Gain de temps estime :[/bold] "
            f"{sa['gain_temps_estime']}",
            title="Analyse strategique",
            border_style="cyan",
        )
    )

    actions = " | ".join(
        f"[{a['label']}]"
        for a in notif["actions_proposees"]
    )

    console.print(
        Panel.fit(
            f"[bold]{notif['titre']}[/bold]\n\n"
            f"{notif['message_vulgarise']}\n\n"
            f"{actions}",
            title=(
                f"Notification "
                f"({notif['canal']}) - "
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


# ---------- Orchestration ----------
def _safe_output_path(
    output_path: Path,
) -> Path:
    """Empeche l'ecriture hors du repertoire courant."""

    resolved = output_path.resolve()
    cwd = Path.cwd().resolve()

    if cwd not in resolved.parents and resolved != cwd:
        raise ValueError(
            "Ecriture refusee hors du repertoire courant : "
            f"{resolved}"
        )

    return resolved


def run(
    input_path: Path,
    provider: str,
    output_path: Optional[Path] = None,
) -> dict:

    if provider not in PROVIDERS:
        raise ValueError(
            f"Provider inconnu : {provider}. "
            f"Disponibles : {sorted(PROVIDERS)}"
        )

    raw_note = _safe_read_text(
        input_path,
        MAX_INPUT_BYTES,
    )

    if not raw_note.strip():
        raise ValueError(
            "Le fichier d'entree est vide."
        )

    raw_response = PROVIDERS[provider](
        raw_note,
        source_label=input_path.name,
    )

    data = _extract_json_object(
        raw_response
    )

    if output_path:

        safe_out = _safe_output_path(
            output_path
        )

        safe_out.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )

        if (
            len(payload.encode("utf-8"))
            > MAX_OUTPUT_BYTES
        ):
            raise ValueError(
                "Sortie trop volumineuse, "
                "ecriture refusee."
            )

        safe_out.write_text(
            payload,
            encoding="utf-8",
        )

    return data


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "OptiPilot-Agent - transforme une directive "
            "brute du responsable en package Ops exploitable."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "samples/input_note_resp.txt"
        ),
        help=(
            "Fichier texte contenant "
            "la directive brute."
        ),
    )

    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDERS),
        default=os.environ.get(
            "OPTIPILOT_PROVIDER",
            "demo",
        ),
        help=(
            "Fournisseur LLM : "
            "demo, groq ou mistral."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Chemin de sortie pour "
            "le JSON genere."
        ),
    )

    args = parser.parse_args()

    try:
        data = run(
            args.input,
            args.provider,
            args.output,
        )

    except Exception as exc:
        print(
            "Erreur OptiPilot-Agent : "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    display_result(data)

    if args.output:
        print(
            f"\nResultat sauvegarde dans "
            f"{args.output}"
        )


if __name__ == "__main__":
    main()