from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from main import (
    call_demo,
    call_groq,
    call_mistral,
    parse_and_validate,
)

# ---------------------------------------------------------------------------
# APPLICATION FASTAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="OptiPilot-Agent API",
    description=(
        "API d'orchestration exécutive pour transformer "
        "une directive brute du responsable en package Ops exploitable."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# PROVIDER AUTORISÉ
# ---------------------------------------------------------------------------

AllowedProvider = Literal[
    "demo",
    "groq",
    "mistral",
]

# ---------------------------------------------------------------------------
# MODÈLE D'ENTRÉE
# ---------------------------------------------------------------------------

class NoteInput(BaseModel):
    """
    Données reçues par l'API.

    Le provider est strictement limité à :
    - demo
    - groq
    - mistral
    """

    note: str = Field(
        ...,
        min_length=1,
        description="Directive brute transmise par le responsable."
    )

    provider: AllowedProvider = Field(
        default="demo",
        description=(
            "Provider autorisé : demo, groq ou mistral."
        ),
    )

# ---------------------------------------------------------------------------
# ROUTE RACINE
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """
    Vérifie que l'API est bien démarrée.
    """

    return {
        "status": "ok",
        "service": "OptiPilot-Agent API",
        "version": "1.0.0",
        "message": "API opérationnelle.",
    }

# ---------------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """
    Endpoint utilisé pour vérifier rapidement l'état de l'API.
    """

    return {
        "status": "healthy",
    }

# ---------------------------------------------------------------------------
# ENDPOINT PRINCIPAL
# ---------------------------------------------------------------------------

@app.post("/analyser")
def analyser(payload: NoteInput):
    """
    Reçoit une directive du responsable et retourne
    le package OptiPilot-Agent au format JSON.
    """

    try:
   
        # 1. Nettoyage de la note

        note = payload.note.strip()

        if not note:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "EMPTY_NOTE",
                    "message": (
                        "La directive du responsable "
                        "ne peut pas être vide."
                    ),
                },
            )

        # 2. Provider déjà validé strictement par Pydantic

        provider = payload.provider

        # 3. Appel du provider

        if provider == "demo":

            raw_response = call_demo(
                note,
                "webhook",
            )

        elif provider == "groq":

            raw_response = call_groq(
                note,
                "webhook",
            )

        elif provider == "mistral":

            raw_response = call_mistral(
                note,
                "webhook",
            )

        # Cette branche ne devrait jamais être atteinte
        # grâce au Literal ci-dessus.
        else:

            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_PROVIDER",
                    "message": (
                        f"Provider non autorisé : '{provider}'."
                    ),
                    "allowed_providers": [
                        "demo",
                        "groq",
                        "mistral",
                    ],
                },
            )
       
        # 4. Parsing et validation du JSON

        result = parse_and_validate(
            raw_response,
        )

        # 5. Retour vers Make 

        return result
        
    # -------------------------------------------------------------------
    # Erreurs HTTP déjà contrôlées
    # -------------------------------------------------------------------

    except HTTPException:
        raise

    # -------------------------------------------------------------------
    # Fichier demo absent
    # -------------------------------------------------------------------

    except FileNotFoundError as exc:

        print(
            f"ERROR /analyser - "
            f"DEMO_FILE_NOT_FOUND: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "DEMO_FILE_NOT_FOUND",
                "message": str(exc),
                "solution": (
                    "Vérifie que le fichier "
                    "samples/output_optipilot_result.json "
                    "est présent dans le dépôt GitHub "
                    "déployé sur Render."
                ),
            },
        ) from exc

    # -------------------------------------------------------------------
    # Erreurs de traitement / validation
    # -------------------------------------------------------------------

    except ValueError as exc:

        print(
            f"ERROR /analyser - "
            f"PROCESSING_ERROR: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROCESSING_ERROR",
                "message": str(exc),
            },
        ) from exc

    # -------------------------------------------------------------------
    # Erreur inattendue
    # -------------------------------------------------------------------

    except Exception as exc:

        print(
            f"ERROR /analyser - "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "type": type(exc).__name__,
                "message": str(exc),
            },
        ) from exc



