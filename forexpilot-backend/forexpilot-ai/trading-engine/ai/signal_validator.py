from ai.gemini_client import generate_json
from ai.market_analysis import build_prompt
from config import settings


def ai_review(symbol, tf, strategy, sig, df) -> tuple[bool, str]:
    """Returns (allowed, note). AI may only VETO a rule-based signal; it can never create or enlarge a trade."""
    out = generate_json(build_prompt(symbol, tf, strategy, sig.direction, sig.reason, df))
    if not out:
        return True, "AI unavailable (ignored)"
    verdict, conf, note = str(out.get("verdict", "neutral")), float(out.get("confidence", 0) or 0), str(out.get("notes", ""))[:200]
    if verdict == "disagree" and conf >= settings.AI_MIN_CONFIDENCE:
        return False, f"AI veto ({conf:.2f}): {note}"
    return True, f"AI {verdict} ({conf:.2f}): {note}"
