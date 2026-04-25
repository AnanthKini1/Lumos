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

from typing import TypedDict


class JudgeResult(TypedDict):
    score: float
    evidence_quotes: list[str]


async def run_judge_call(
    judge_prompt: str,
    transcript_text: str,
) -> JudgeResult:
    """Make one judge LLM call for a single cognitive dimension."""
    raise NotImplementedError
