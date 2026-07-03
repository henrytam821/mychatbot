# AGENTS.md

Python chatbot demo — FastAPI backend calling OpenRouter API.

## Quick start

```bash
python -m venv .venv && .venv\Scripts\Activate
pip install -r requirements.txt
cp .env.example .env   # edit .env with your OpenRouter API key
uvicorn main:app --reload
```

Open http://localhost:8000

## Commands

| Action | Command |
|---|---|
| Dev server | `uvicorn main:app --reload` |
| Install deps | `pip install -r requirements.txt` |

## Project structure

```
main.py          — FastAPI app, /chat endpoint, OpenRouter integration
templates/
  index.html     — single-page chat UI
requirements.txt
.env.example
```

## Key facts

- API key goes in `.env` as `OPENROUTER_API_KEY` (get one at https://openrouter.ai/keys)
- Default model: `openai/gpt-4o-mini` — override via `OPENROUTER_MODEL` in `.env`
- Server runs on `http://localhost:8000`
- Chat endpoint: `POST /chat` with `{"message": "..."}` → `{"reply": "..."}`
- No database, no auth, no streaming
