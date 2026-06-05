import os
import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Cloth Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

# ── Request models ────────────────────────────────────────────────────

class PromptRequest(BaseModel):
    keyword: str          # user's short input, e.g. "Tokyo night"

class ImageRequest(BaseModel):
    prompt: str           # expanded English prompt from Claude
    width: int = 1024
    height: int = 768
    model: str = "flux-realism"

# ── Routes ───────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/expand-prompt")
async def expand_prompt(req: PromptRequest):
    """
    Send a short keyword to Claude.
    Claude returns a detailed English image generation prompt.
    """
    if not CLAUDE_API_KEY:
        raise HTTPException(status_code=500, detail="CLAUDE_API_KEY not configured")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    system = (
        "You are an expert image prompt engineer. "
        "When given a short keyword or phrase, you expand it into a single, "
        "detailed English image generation prompt. "
        "The prompt should be vivid, specific, and optimized for photorealistic output. "
        "Focus on architectural subjects, lighting, atmosphere, and camera style. "
        "Always end with: photorealistic, architectural photography, 8k, high detail. "
        "Return ONLY the prompt text, no explanation, no quotes, no extra formatting."
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": req.keyword}]
    )

    expanded = message.content[0].text.strip()
    return {"expanded_prompt": expanded}


@app.post("/generate-image")
async def generate_image(req: ImageRequest):
    """
    Build a Pollinations.ai URL from the expanded prompt and return it directly.
    The frontend loads the image — no server-side ping needed.
    """
    safe_prompt = req.prompt.replace(" ", "%20").replace(",", "%2C")
    url = (
        f"https://image.pollinations.ai/prompt/{safe_prompt}"
        f"?model={req.model}"
        f"&width={req.width}"
        f"&height={req.height}"
        f"&nologo=true"
        f"&enhance=true"
        f"&seed={int(__import__('time').time())}"
    )
    return {"image_url": url}
