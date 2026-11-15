# DEPLOYMENT — Abandoned, not forgotten

Step-by-step guide to put the site live. Choose **Option A** (single service, simplest) or **Option B** (static frontend + API separately).

## Table of contents

1. [Before you deploy](#1-before-you-deploy)
2. [Option A — one service (recommended)](#2-option-a--one-service-recommended)
3. [Option B — static frontend + API separately](#3-option-b--static-frontend--api-separately)
4. [Environment variables](#4-environment-variables)
5. [Post-deploy checks](#5-post-deploy-checks)

---

## 1. Before you deploy

### Replace the placeholder domain

The SEO/GEO files ship with `YOUR-SITE.vercel.app`. Replace it with your real domain in all four places:

- `frontend/robots.txt` — sitemap URL
- `frontend/sitemap.xml` — the page URL
- `frontend/llms.txt` — all links
- `frontend/index.html` — `og:url`, `og:image`, `twitter:image`, `<link rel="canonical">`

One-liner to do it at once (from the project root):

```bash
grep -rl "YOUR-SITE.vercel.app" frontend | xargs sed -i 's/YOUR-SITE.vercel.app/YOUR-DOMAIN/g'
```

(On Windows Git Bash, use the same command; replace `YOUR-DOMAIN` with e.g. `abandoned-not-forgotten.vercel.app`.)

### Check the API key

- The key lives in `backend/.env` locally, but **never commit it**. On the host it must be set as an environment variable instead (see section 4).
- Groq key (`gsk_...`): make sure a model is enabled at https://console.groq.com/settings/limits.
- xAI key (`xai-...`): recommended — it unlocks the AI web search toggle.

### Test locally one last time

```bash
cd backend
.venv/Scripts/activate
uvicorn main:app
```

Open http://localhost:8000 — site loads, `/api/health` returns `ok`, and the Researcher chat replies.

---

## 2. Option A — one service (recommended)

The FastAPI server already serves the frontend from `/`. Deploy the whole project as one Python web service on a host with Python support.

### Render (free tier works)

1. Push the repo to GitHub.
2. On https://render.com: **New → Web Service → connect your repo**.
3. Settings:
   - **Root directory:** `backend`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add the environment variable from section 4.
5. **Deploy.** Your site is live at `https://YOUR-APP.onrender.com`.

### Railway

1. Push the repo to GitHub, connect it on https://railway.app (**New Project → Deploy from GitHub repo**).
2. Add a `Procfile` in the repo root (or `backend/`):
   ```
   web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
3. In **Variables**, add the key from section 4.
4. Railway auto-detects and deploys. The domain is under **Settings → Networking**.

### Fly.io

1. Install the Fly CLI (`flyctl`) and log in.
2. From the project root, create `fly.toml`:
   ```toml
   app = "abandoned-not-forgotten"
   primary_region = "iad"

   [build]

   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = "stop"
     auto_start_machines = true
     min_machines_running = 0

   [env]
     PORT = "8000"
   ```
   Then add `Procfile`:
   ```
   web: cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
   ```
3. Set the key: `fly secrets set GROK_API_KEY="..."` then `fly deploy`.

---

## 3. Option B — static frontend + API separately

Only if you want the frontend on a static host. Downside: two deployments and CORS.

### Frontend (Vercel / Netlify / GitHub Pages)

1. Deploy the `frontend/` folder as the site root (on Vercel: **Root Directory** = `frontend`, no build command).
2. Point the chat at your backend URL. In `frontend/index.html`, find the fetch call in the chat submit handler:
   ```js
   fetch('/api/agent', ...)
   ```
   and change it to your full backend URL, e.g.
   ```js
   fetch('https://your-api.onrender.com/api/agent', ...)
   ```
   Same for the `/api/health` fetch.
3. Deploy the backend as in Option A (Render/Railway/Fly), and add CORS there. In `backend/main.py`:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   app.add_middleware(CORSMiddleware, allow_origins=["https://YOUR-FRONTEND-DOMAIN"], allow_methods=["*"], allow_headers=["*"])
   ```

---

## 4. Environment variables

On every host, set this one variable (same as `backend/.env` locally):

| Variable | Example value | Notes |
|---|---|---|
| `GROK_API_KEY` | `xai-...` or `gsk_...` | required — the agent won't work without it |
| `GROK_MODEL` | `grok-4.7` | optional, only for xAI keys |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | optional, only for Groq keys |

Keep `GROK_API_KEY` out of git — add `backend/.env` to `.gitignore` if you haven't:

```
backend/.env
```

---

## 5. Post-deploy checks

1. **Site** — home page loads, 3D Moon/Mars renders, videos play.
2. **Agent** — open the Researcher tab, ask "Why did NASA switch off ALSEP?" and get a reply. Visit `/api/health` and confirm `"agent": true`.
3. **AI search** — if you used an xAI key, the toggle is enabled and returns answers with fresh web facts.
4. **SEO** — view-source on the live page: canonical and `og:image` show your real domain.
5. **GEO** — `https://YOUR-DOMAIN/robots.txt`, `/sitemap.xml` and `/llms.txt` all resolve and use the real domain.
6. **AI visibility** — submit `https://YOUR-DOMAIN/llms.txt` in ChatGPT / Perplexity search, and check Google Search Console → URL Inspection for indexability.

Done — the machines are online.
