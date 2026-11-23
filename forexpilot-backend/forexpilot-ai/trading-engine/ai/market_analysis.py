import pandas as pd


def build_prompt(symbol: str, tf: str, strategy: str, direction: str, reason: str, df: pd.DataFrame) -> str:
    c = df["close"].tail(30).round(5).tolist()
    return (
        "You are a cautious forex analyst reviewing a signal produced by a rule-based system. "
        "You can only agree, disagree or stay neutral; you cannot change levels.\n"
        f"Pair {symbol}, timeframe {tf}, strategy {strategy}, proposed direction {direction}. Rule trigger: {reason}.\n"
        f"Last 30 closes (oldest first): {c}\n"
        'Reply ONLY as JSON: {"verdict":"agree|disagree|neutral","confidence":0.0-1.0,"notes":"one short sentence"}'
    )
