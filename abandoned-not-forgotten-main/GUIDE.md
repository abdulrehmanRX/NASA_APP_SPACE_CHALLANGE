# GUIDE — Abandoned, not forgotten

Everything you need to run, use and deploy the site. If you just want the short version, see [README.md](README.md).

## Table of contents

1. [What the project is](#1-what-the-project-is)
2. [Setup (first time)](#2-setup-first-time)
3. [Running the server](#3-running-the-server)
4. [The Mission Researcher agent](#4-the-mission-researcher-agent)
5. [API reference](#5-api-reference)
6. [Configuration](#6-configuration)
7. [Editing the site](#7-editing-the-site)
8. [Deploying](#8-deploying)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. What the project is

A single-page site that tells the stories of the machines astronauts left on the Moon and Mars, over real 3D worlds (three.js), with an AI **Mission Researcher** chat agent.

- **Frontend** — `frontend/index.html`. Plain HTML/CSS/JS, no framework, no build step. three.js (CDN), Web Audio ambient score, scroll-driven camera.
- **Backend** — `backend/` (FastAPI). Serves the frontend and exposes two API endpoints:
  - `POST /api/agent` — the researcher chat
  - `GET /api/health` — status check
- **Agent** — `backend/agent.py`. Talks to either the xAI (Grok) API or the Groq API, auto-detected from your key.

## 2. Setup (first time)

Prerequisites: Python 3.9+ (3.12 recommended).

```bash
cd backend

# 1. create a virtual environment
python -m venv .venv

# 2. activate it
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. install dependencies
pip install -r requirements.txt

# 4. create your key file
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
```

**5. Add your API key** — open `backend/.env` and set `GROK_API_KEY`:

| Key | Where to get it | Gives you |
|---|---|---|
| `xai-...` | https://console.x.ai | agent **and** live AI web search |
| `gsk_...` | https://console.groq.com/keys | agent only (no web search) |

If you use a Groq key, also make sure at least one model is enabled for your org at https://console.groq.com/settings/limits — otherwise every request returns `403 model_permission_blocked_org`.

The provider is detected from the key prefix, so you never need to configure anything else.

## 3. Running the server

```bash
cd backend
.venv/Scripts/activate
uvicorn main:app --reload
```

Open **http://localhost:8000** — the site loads from the FastAPI server, and the Researcher tab talks to `/api/agent`.

Check the health endpoint at http://localhost:8000/api/health:

```json
{"ok": true, "agent": true, "provider": "groq", "search": false}
```

- `agent: true` — a usable API key is configured.
- `search: true` — AI web search is available (xAI keys only).

## 4. The Mission Researcher agent

Open the **Researcher** tab in the nav and ask about any machine. It answers from the mission facts in its system prompt (ALSEP, the LM descent stages, Sojourner, and the rest).

- **AI search toggle** — with an xAI key, the agent can look up fresh facts on the web. The checkbox shows automatically when the backend supports it; with a Groq key it is disabled with a note.
- **Ask the researcher buttons** — every story panel, gallery photo and "More left behind" drawer entry has one. Clicking it opens the chat with the question pre-filled and sends it.
- **History** — the conversation is kept in the browser tab and sent with each message, so the agent remembers the current chat.

## 5. API reference

### `POST /api/agent`

Request:

```json
{
  "message": "Why did NASA switch off ALSEP?",
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "search": true
}
```

- `message` — the new user message (required).
- `history` — previous turns, oldest first (optional).
- `search` — allow live web search (optional, default `true`; ignored for Groq keys).

Response:

```json
{"reply": "NASA switched off ALSEP in September 1977 ..."}
```

Errors: `502` if the model provider fails, `503` if the backend has no key. The error message is shown in the chat bubble.

### `GET /api/health`

```json
{"ok": true, "agent": true, "provider": "xai", "search": true}
```

## 6. Configuration

All settings live in `backend/.env`:

| Variable | Default | Purpose |
|---|---|---|
| `GROK_API_KEY` | — | your xAI or Groq key (required) |
| `GROK_MODEL` | `grok-4.7` | model used with xAI |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | model used with Groq |

## 7. Editing the site

- **Text, layout, chat UI** — everything is in `frontend/index.html` (one file).
- **Images** — `frontend/assets/img/` (planet textures, machine photos, video posters). All images use `loading="lazy" decoding="async"`; keep those attributes when you swap files.
- **Videos** — `frontend/vid/`. Stock footage, illustrative only.
- **Adding an "Ask the researcher" button** — add an element with class `rq` and a `data-q` attribute:

  ```html
  <button class="rq" data-q="How long did Sojourner drive?">Ask the researcher</button>
  ```

  No other wiring needed; the click handler in `index.html` picks it up.
- **Agent knowledge** — the system prompt in `backend/agent.py` (`SYSTEM_PROMPT`). Edit it there to change what the researcher knows off the top of its head.

## 8. Deploying

The repo ships with SEO/GEO files that use the placeholder `YOUR-SITE.vercel.app`. Before deploying, replace it with your real domain in:

- `frontend/robots.txt` (sitemap URL)
- `frontend/sitemap.xml`
- `frontend/llms.txt` (all links)
- `frontend/index.html` — `<link rel="canonical">`, `og:url`, `og:image`, `twitter:image`

Deployment options:

- **Any static host** (Vercel, Netlify, GitHub Pages): the frontend works as pure static files, but then `/api/agent` won't exist — deploy the backend too (Render, Railway, Fly.io) and point `frontend/index.html`'s fetch at the full backend URL, or serve both from one host.
- **One host with Python support** (Render, Railway, Fly.io): run `uvicorn main:app` from `backend/` — the backend serves the frontend automatically, so a single deployment covers everything.

Note: the agent endpoints need the API key on the server, so set `GROK_API_KEY` as an environment variable on your host (never commit `backend/.env`).

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `403 model_permission_blocked_org` in the chat | Your Groq org hasn't enabled the model | Enable a model at https://console.groq.com/settings/limits |
| `400 Incorrect API key` from xAI | The key is a Groq key (`gsk_...`), not an xAI key (`xai-...`) | Get an xAI key from https://console.x.ai, or keep the Groq key (agent still works, no web search) |
| `503` reply "no API key configured" | `GROK_API_KEY` missing or still the placeholder in `.env` | Set the key in `backend/.env` and restart the server |
| AI search toggle is disabled | You're using a Groq key | Use an xAI key for web search |
| Port 8000 already in use | Another server is running | Stop it, or run `uvicorn main:app --port 8001` |
| 3D scene is black | Textures not loaded (network) | Check the browser console; textures live in `frontend/assets/img/` |
| Site loads but chat never answers | Backend not running | Start uvicorn from `backend/` and check `/api/health` first |
