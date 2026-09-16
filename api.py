from fastapi import FastAPI
from pydantic import BaseModel
from main import call_demo, call_groq, parse_and_validate

app = FastAPI()

class NoteInput(BaseModel):
    note: str
    provider: str = "demo"

@app.get("/")
def home():
    return {"status": "ok", "message": "API OptiPilot-Agent opérationnelle. Utilisez /docs pour tester."}

@app.post("/analyser")
def analyser(payload: NoteInput):
    raw = call_demo(payload.note, "webhook") if payload.provider == "demo" \
        else call_groq(payload.note, "webhook")
    return parse_and_validate(raw)