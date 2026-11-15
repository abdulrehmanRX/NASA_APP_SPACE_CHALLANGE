"""FastAPI app: serves the frontend and exposes the Mission Researcher agent."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import PROVIDER, AgentError, key_ready, research, search_supported

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="Abandoned, not forgotten")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    search: bool = True


@app.get("/api/health")
def health():
    return {"ok": True, "agent": key_ready(), "provider": PROVIDER, "search": search_supported()}


@app.post("/api/agent")
async def agent(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")
    try:
        reply = await research(req.message, [m.model_dump() for m in req.history], req.search)
    except AgentError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e}")
    return {"reply": reply}


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
