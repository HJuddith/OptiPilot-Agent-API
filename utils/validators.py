import json


# ============================================================
# SCHÉMA ATTENDU
# ============================================================

REQUIRED_TOP_LEVEL_KEYS = {
    "meta",
    "strategic_analysis",
    "cahier_des_charges_technique",
    "prompt_systeme_genere",
    "notification",
}


# ============================================================
# ACTIONS SLACK
# ============================================================

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


# ============================================================
# NORMALISATION DES ACTIONS
# ============================================================

def normalize_actions(notification: dict) -> None:
    """
    Garantit que notification.actions_proposees
    contient exactement 3 actions valides.
    """

    actions = notification.get(
        "actions_proposees"
    )

    if not isinstance(actions, list):
        actions = []

    valid_actions = []

    for action in actions:

        if not isinstance(action, dict):
            continue

        label = str(
            action.get("label", "")
        ).strip()

        action_id = str(
            action.get("action_id", "")
        ).strip()

        if label and action_id:
            valid_actions.append(
                {
                    "label": label,
                    "action_id": action_id,
                }
            )

    # Si l'IA demande explicitement une clarification,
    # on utilise les actions adaptées.
    clarification_required = any(
        action.get("action_id")
        == "request_clarification"
        for action in valid_actions
    )

    if clarification_required:
        notification["actions_proposees"] = (
            CLARIFICATION_ACTIONS.copy()
        )
    else:
        notification["actions_proposees"] = (
            DEFAULT_QVT_ACTIONS.copy()
        )


# ============================================================
# EXTRACTION DU JSON
# ============================================================

def extract_json_object(
    raw_content: str,
) -> dict:
    """
    Transforme la réponse brute du LLM en objet Python
    et vérifie la présence des champs obligatoires.
    """

    raw_content = raw_content.strip()

    if not raw_content:
        raise ValueError(
            "La réponse du modèle est vide."
        )

    # --------------------------------------------------------
    # Première tentative : JSON pur
    # --------------------------------------------------------

    try:
        data = json.loads(raw_content)

    except json.JSONDecodeError:

        # ----------------------------------------------------
        # Deuxième tentative :
        # récupérer uniquement la partie JSON
        # ----------------------------------------------------

        start = raw_content.find("{")
        end = raw_content.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                "Impossible de trouver un objet JSON valide "
                "dans la réponse du modèle."
            )

        json_part = raw_content[
            start:end + 1
        ]

        try:
            data = json.loads(json_part)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"JSON invalide retourné par le modèle : {exc}"
            ) from exc

    # ========================================================
    # VALIDATION DE LA STRUCTURE
    # ========================================================

    if not isinstance(data, dict):
        raise ValueError(
            "La réponse du modèle doit être un objet JSON."
        )

    missing_keys = (
        REQUIRED_TOP_LEVEL_KEYS
        - set(data.keys())
    )

    if missing_keys:
        raise ValueError(
            "Champs obligatoires manquants : "
            + ", ".join(
                sorted(missing_keys)
            )
        )

    # ========================================================
    # VALIDATION NOTIFICATION
    # ========================================================

    notification = data.get(
        "notification"
    )

    if not isinstance(notification, dict):
        raise ValueError(
            "Le champ notification doit être un objet."
        )

    # ========================================================
    # NORMALISATION SLACK
    # ========================================================

    normalize_actions(
        notification
    )

    return data

