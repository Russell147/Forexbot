import json

import requests

from config import settings


def generate_json(prompt: str, timeout: int = 15) -> dict | None:
    """Ask Gemini for a JSON answer. Returns None on any failure (AI is advisory; failure never blocks the engine)."""
    if not settings.GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    try:
        r = requests.post(url, headers={"x-goog-api-key": settings.GEMINI_API_KEY}, timeout=timeout,
                          json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}})
        r.raise_for_status()
        return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    except Exception:
        return None
