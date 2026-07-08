import os
from pathlib import Path
# Get the directory where main.py actually lives
BASE_DIR = Path(__file__).resolve().parent
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 1. Get the directory where main.py actually lives
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

POPULAR_MODELS = [
    {"id": "openai/gpt-4o-mini"},
    {"id": "openai/gpt-4o"},
    {"id": "openai/o3-mini"},
    {"id": "anthropic/claude-sonnet-4-20250514"},
    {"id": "anthropic/claude-3.5-haiku"},
    {"id": "google/gemini-2.5-flash"},
    {"id": "google/gemini-2.5-pro"},
    {"id": "meta-llama/llama-4-maverick"},
    {"id": "deepseek/deepseek-chat"},
    {"id": "qwen/qwen-3-235b-a22b"},
    {"id": "mistralai/mistral-small-3.1-24b"},
]


class ChatRequest(BaseModel):
    message: str
    model: str = OPENROUTER_MODEL
    api_key: str = ""


class ModelsRequest(BaseModel):
    api_key: str = ""


class ChatResponse(BaseModel):
    reply: str


def _resolve_key(provided: str) -> str:
    return provided or OPENROUTER_API_KEY


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_model": OPENROUTER_MODEL})


@app.post("/models")
async def list_models(req: ModelsRequest):
    """Return models from OpenRouter using provided API key, falling back to curated list."""
    key = _resolve_key(req.api_key)
    if not key:
        return {"models": POPULAR_MODELS, "default_model": OPENROUTER_MODEL}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                OPENROUTER_MODELS_URL,
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            if resp.status_code == 401:
                return {"models": POPULAR_MODELS, "default_model": OPENROUTER_MODEL, "error": "Invalid API key, showing curated list"}
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("data", []):
                mid = m.get("id")
                if not mid:
                    continue
                pricing = m.get("pricing", {})
                free = all(v == "0" for v in pricing.values())
                models.append({"id": mid, "free": free})
            if models:
                return {"models": models, "default_model": OPENROUTER_MODEL}
    except Exception:
        pass
    return {"models": POPULAR_MODELS, "default_model": OPENROUTER_MODEL}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    key = _resolve_key(req.api_key)
    if not key:
        raise HTTPException(status_code=400, detail="OpenRouter API key is required. Paste it in the API Key field or set OPENROUTER_API_KEY in .env")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": req.model,
        "messages": [{"role": "user", "content": req.message}],
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(OPENROUTER_CHAT_URL, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        detail = "OpenRouter request failed"
        try:
            body = e.response.json()
            err = body.get("error", {})
            detail = err.get("metadata", {}).get("raw", err.get("message", e.response.text[:300]))
        except Exception:
            detail = e.response.text[:300]
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error contacting OpenRouter: {e}")
    except (KeyError, IndexError, ValueError):
        raise HTTPException(status_code=502, detail="Unexpected response format from OpenRouter")

    return ChatResponse(reply=reply)
if __name__ == "__main__":
    import uvicorn
    # 💡 關鍵：在容器內 Host 必須是 0.0.0.0，才能讓外部（Portainer/K8s）存取
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
