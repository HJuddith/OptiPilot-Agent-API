import json


def escape_json(value: str) -> str:
    """
    Échappe une valeur pour pouvoir l'utiliser
    correctement dans un JSON Slack.
    """

    return json.dumps(
        str(value),
        ensure_ascii=False,
    )[1:-1]


def build_slack_blocks(notification: dict) -> dict:
    """
    Construit les Slack Block Kit à partir
    de la notification générée par OptiPilot-Agent.
    """

    actions = notification.get(
        "actions_proposees",
        [],
    )

    # Sécurité supplémentaire :
    # Slack attend exactement les actions disponibles.
    actions = [
        action
        for action in actions
        if isinstance(action, dict)
        and action.get("label")
        and action.get("action_id")
    ]

    elements = []

    for index, action in enumerate(actions):
        button = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": str(
                    action["label"]
                ),
                "emoji": True,
            },
            "action_id": str(
                action["action_id"]
            ),
        }

        # Premier bouton en principal.
        if index == 0:
            button["style"] = "primary"

        # Dernier bouton en danger.
        elif index == len(actions) - 1:
            button["style"] = "danger"

        elements.append(button)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": str(
                    notification.get(
                        "titre",
                        "Notification OptiPilot-Agent",
                    )
                ),
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": str(
                    notification.get(
                        "message_vulgarise",
                        "",
                    )
                ),
            },
        },
        {
            "type": "divider",
        },
    ]

    # On ajoute le bloc actions uniquement
    # s'il contient des boutons valides.
    if elements:
        blocks.append(
            {
                "type": "actions",
                "elements": elements,
            }
        )

    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Bonne continuation à tous._",
                }
            ],
        }
    )

    return {
        "blocks": blocks
    }


def build_slack_payload(
    notification: dict,
) -> str:
    """
    Retourne le payload Slack sous forme
    de JSON prêt à être envoyé.
    """

    blocks = build_slack_blocks(
        notification
    )

    return json.dumps(
        blocks,
        ensure_ascii=False,
        indent=2,
    )

