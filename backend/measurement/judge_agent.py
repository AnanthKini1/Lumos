"""
WS-A — Judge agent: single LLM call per cognitive dimension.

Owns one responsibility: given a judge prompt for one cognitive dimension and
the transcript text to evaluate, make one LLM call and return a structured
score (0-10) plus 1-2 cited quotes from the transcript as evidence.

This is the leaf-level call that scorer.py invokes for each dimension. It knows
nothing about which dimension it's scoring or how results aggregate — that logic
belongs to scorer.py.

Responsibilities:
- Inject the dimension-specific judge prompt (from judge_prompts.py)
- Inject the transcript excerpt to evaluate
- Enforce the MAX_TOKENS_JUDGE cap
- Parse and return the structured {score, evidence_quotes} response

Does NOT know about:
- Which cognitive dimension is being scored (scorer.py owns that mapping)
- How individual scores combine into CognitiveScores (scorer.py)
- Verdict logic (verdict.py)
- The simulation itself (simulation/)
"""

import json
from typing import TypedDict

import anthropic

from config import ANTHROPIC_API_KEY, MAX_TOKENS_JUDGE, MODEL_ID


class JudgeResult(TypedDict):
    score: float
    evidence_quotes: list[str]


async def run_judge_call(
    judge_prompt: str,
    transcript_text: str,
) -> JudgeResult:
    """Make one judge LLM call for a single cognitive dimension.

    Args:
        judge_prompt: The full dimension-specific prompt from judge_prompts.py.
        transcript_text: JSON-serialized transcript excerpt to evaluate.

    Returns:
        JudgeResult with score (0-10) and 1-2 evidence_quotes from the transcript.

    Raises:
        ValueError: If the model response cannot be parsed as valid JSON with
                    the required keys.
    """
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    user_message = (
        "Here is the transcript to evaluate:\n\n"
        f"{transcript_text}\n\n"
        "Return valid JSON only — no other text."
    )

    message = await client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS_JUDGE,
        system=judge_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = message.content[0].text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Judge response was not valid JSON: {raw_text!r}"
        ) from exc

    if "score" not in parsed or "evidence_quotes" not in parsed:
        raise ValueError(
            f"Judge response missing required keys. Got: {list(parsed.keys())}"
        )

    return JudgeResult(
        score=float(parsed["score"]),
        evidence_quotes=list(parsed["evidence_quotes"]),
    )
