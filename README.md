# Cloth Portal · AI Reveal

A cloth simulation that uses Claude AI to expand a short keyword into a detailed
image prompt, generates the image via Pollinations.ai, and maps it onto a
physically-simulated cloth that you can drag and reveal with your hand.

---

## Project structure

```
cloth-portal-project/
├── main.py               # FastAPI backend (Railway)
├── requirements.txt
├── Procfile
├── railway.json
├── .env.example
├── .gitignore
└── frontend/
    └── index.html        # p5.js cloth simulation (Netlify)
```

---

## Deploy — Step by step

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "init cloth portal"
git remote add origin https://github.com/YOUR_USERNAME/cloth-portal.git
git push -u origin main
```

### 2. Deploy backend to Railway

1. Go to https://railway.app → **New Project** → **Deploy from GitHub repo**
2. Select this repo
3. Railway will auto-detect `Procfile` and install `requirements.txt`
4. Go to your project → **Variables** tab → add:
   ```
   CLAUDE_API_KEY = sk-ant-xxxxxxxxxxxxxxxx
   ```
5. Click **Deploy** — wait ~1 min
6. Go to **Settings** → **Networking** → **Generate Domain**
7. Copy the URL, e.g. `https://cloth-portal-production.railway.app`

### 3. Update frontend with your Railway URL

Open `frontend/index.html`, find line:
```js
const BACKEND_URL = "https://YOUR_RAILWAY_APP.railway.app";
```
Replace with your actual Railway URL.

### 4. Deploy frontend to Netlify

**Option A — drag and drop (fastest):**
1. Go to https://netlify.com → **Add new site** → **Deploy manually**
2. Drag the `frontend/` folder into the upload area
3. Done — Netlify gives you a URL like `https://xxx.netlify.app`

**Option B — connect GitHub:**
1. Netlify → **Add new site** → **Import from Git**
2. Select this repo
3. Set **Publish directory** to `frontend`
4. Deploy

---

## How to use

1. Open the Netlify URL on your phone
2. Allow camera permission
3. Type a scene in the bottom-left input (e.g. "abandoned temple in fog")
4. Click **✦ Generate with AI**
5. Claude expands the prompt → Pollinations generates the image → cloth updates
6. Drag the cloth to reveal the image beneath

---

## Local development

```bash
# Backend
pip install -r requirements.txt
cp .env.example .env        # fill in CLAUDE_API_KEY
uvicorn main:app --reload --port 8000

# Frontend — just open in browser
open frontend/index.html
# Update BACKEND_URL to http://localhost:8000
```
