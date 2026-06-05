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
HF_TOKEN       = os.environ.get("HF_TOKEN")
HF_MODEL       = "black-forest-labs/FLUX.1-schnell"
HF_URL         = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

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


@app.get("/test-network")
async def test_network():
    """Test if Railway can reach external services."""
    results = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, url in [
            ("huggingface", "https://api-inference.huggingface.co"),
            ("google", "https://www.google.com"),
        ]:
            try:
                r = await client.get(url)
                results[name] = f"OK ({r.status_code})"
            except Exception as e:
                results[name] = f"FAILED: {str(e)[:80]}"
    return results


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
    """Generate an image via Hugging Face Inference API, return as base64 data URL."""
    if not HF_TOKEN:
        raise HTTPException(status_code=500, detail="HF_TOKEN not configured")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": req.prompt,
        "parameters": {
            "width": req.width,
            "height": req.height,
            "num_inference_steps": 4,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(HF_URL, headers=headers, json=payload)

            # Model may be loading — retry once after 20s
            if response.status_code == 503:
                import asyncio
                await asyncio.sleep(20)
                response = await client.post(HF_URL, headers=headers, json=payload)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"HF API error {response.status_code}: {response.text[:200]}"
                )

            # Return image as base64 data URL so frontend can load without CORS issues
            img_bytes = response.content
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{b64}"
            return {"image_url": data_url}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image generation timed out")

