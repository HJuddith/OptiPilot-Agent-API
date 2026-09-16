from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from main import call_demo, call_groq, call_mistral, extract_json_object

app = FastAPI(title="OptiPilot-Agent API", version="1.0.0")

MAX_NOTE_CHARS = 20_000

PROVIDERS = {
    "demo": call_demo,
    "groq": call_groq,
    "mistral": call_mistral,
}


class NoteInput(BaseModel):
    note: str = Field(..., min_length=1, max_length=MAX_NOTE_CHARS)
    provider: Literal["demo", "groq", "mistral"] = "demo"


@app.get("/")
def root():
    return {"status": "ok", "service": "OptiPilot-Agent API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyser")
def analyser(payload: NoteInput):
    note = payload.note.strip()
    if not note:
        raise HTTPException(400, detail={"error": "EMPTY_NOTE"})

    try:
        raw_response = PROVIDERS[payload.provider](note, "webhook")
        return extract_json_object(raw_response)

    except HTTPException:
        raise

    except FileNotFoundError as exc:
        print(f"ERROR /analyser - DEMO_FILE_NOT_FOUND: {exc}")
        raise HTTPException(500, detail={"error": "DEMO_FILE_NOT_FOUND"}) from exc

    except ValueError as exc:
        print(f"ERROR /analyser - PROCESSING_ERROR: {exc}")
        raise HTTPException(500, detail={"error": "PROCESSING_ERROR"}) from exc

    except Exception as exc:
        print(f"ERROR /analyser - {type(exc).__name__}: {exc}")
        raise HTTPException(500, detail={"error": "INTERNAL_SERVER_ERROR"}) from exc