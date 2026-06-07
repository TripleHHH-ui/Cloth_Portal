import os
import base64
import httpx
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
FAL_API_KEY    = os.environ.get("FAL_API_KEY")
FAL_URL        = "https://fal.run/fal-ai/flux/schnell"

# ── Request models ────────────────────────────────────────────────────

class PromptRequest(BaseModel):
    keyword: str

class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 768

# ── Routes ───────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/expand-prompt")
async def expand_prompt(req: PromptRequest):
    """Send a short keyword to Claude, get back a detailed image prompt."""
    if not CLAUDE_API_KEY:
        raise HTTPException(status_code=500, detail="CLAUDE_API_KEY not configured")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    system = (
        "You are an expert image prompt engineer. "
        "When given a short keyword or phrase, expand it into a single detailed "
        "English image generation prompt. Be vivid and specific. "
        "Focus on architecture, lighting, atmosphere, and camera style. "
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
    """Generate image via fal.ai FLUX, return as base64 data URL."""
    if not FAL_API_KEY:
        raise HTTPException(status_code=500, detail="FAL_API_KEY not configured")

    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": req.prompt,
        "image_size": {"width": req.width, "height": req.height},
        "num_inference_steps": 4,
        "num_images": 1,
        "enable_safety_checker": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(FAL_URL, headers=headers, json=payload)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"fal.ai error {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            # fal.ai returns { images: [{ url: "https://..." }] }
            image_url = data["images"][0]["url"]

            # Fetch image and return as base64 to avoid frontend CORS issues
            img_response = await client.get(image_url)
            b64 = base64.b64encode(img_response.content).decode("utf-8")
            return {"image_url": f"data:image/jpeg;base64,{b64}"}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image generation timed out")
