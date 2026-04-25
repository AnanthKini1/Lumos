"""
WS-A — Conversation scorer. This is the entry point for Seam 1.

Exposes score_conversation() — the single function that WS-B's pipeline.py
calls after conversations complete. WS-B imports nothing else from measurement/.

Internally, this module:
  - Calls judge_agent.run_judge_call() once per cognitive dimension (parallelized)
  - Aggregates individual dimension scores into a CognitiveScores record
  - Selects 2-3 standout quotes from the monologues
  - Generates a synthesis paragraph via one final summarizer LLM call
  - Returns (CognitiveScores, list[StandoutQuote], synthesis_paragraph)

WS-B's pipeline does not know how scoring works. It calls score_conversation()
and gets back a result. That function signature is the entire contract.
"""

import asyncio
import json

import anthropic

_JUDGE_SEMAPHORE = asyncio.Semaphore(4)

from config import ANTHROPIC_API_KEY, API_MAX_RETRIES, MAX_TOKENS_JUDGE, MODEL_ID
from measurement.judge_agent import JudgeResult, run_judge_call
from measurement.judge_prompts import (
    AMBIVALENCE_PRESENCE_PROMPT,
    ENGAGEMENT_DEPTH_PROMPT,
    IDENTITY_THREAT_PROMPT,
    MEMORY_RESIDUE_PROMPT,
    MOTIVATED_REASONING_PROMPT,
    PERSISTENCE_PROMPT,
    PUBLIC_PRIVATE_GAP_PROMPT,
)
from models import (
    CognitiveScores,
    ConversationTurn,
    CoolingOff,
    PersistenceResult,
    StandoutQuote,
)

_SYNTHESIS_MAX_TOKENS = 300
_STANDOUT_COUNT = 3


def _serialize_turns(turns: list[ConversationTurn]) -> str:
    """Serialize turns to JSON string for injection into judge prompts."""
    return json.dumps(
        [turn.model_dump() for turn in turns],
        indent=2,
        default=str,
    )


def _serialize_cooling_off(cooling_off: CoolingOff) -> str:
    return json.dumps(cooling_off.model_dump(), indent=2, default=str)


def _persistence_from_score(score: float) -> PersistenceResult:
    """Map a 0-10 persistence judge score to a PersistenceResult enum value."""
    if score >= 6.0:
        return PersistenceResult.HELD
    if score >= 3.0:
        return PersistenceResult.PARTIALLY_REVERTED
    return PersistenceResult.FULLY_REVERTED


def _select_standout_quotes(
    turns: list[ConversationTurn],
    count: int = _STANDOUT_COUNT,
) -> list[StandoutQuote]:
    """
    Select the most interesting quotes from the conversation.

    Strategy: prefer turns where identity was threatened or emotional intensity
    is high. Fall back to picking evenly spaced turns if needed.
    """
    candidates: list[StandoutQuote] = []

    for turn in turns:
        po = turn.persona_output
        if po.identity_threat.threatened or po.emotional_reaction.intensity >= 7:
            candidates.append(
                StandoutQuote(
                    turn=turn.turn_number,
                    type="monologue",
                    text=po.internal_monologue[:300],
                    annotation=(
                        f"Emotion: {po.emotional_reaction.primary_emotion.value} "
                        f"(intensity {po.emotional_reaction.intensity})"
                    ),
                )
            )

    # If we have enough, return top `count`
    if len(candidates) >= count:
        return candidates[:count]

    # Fill remaining slots with public responses from evenly spaced turns
    existing_turn_numbers = {q.turn for q in candidates}
    for turn in turns:
        if turn.turn_number not in existing_turn_numbers:
            candidates.append(
                StandoutQuote(
                    turn=turn.turn_number,
                    type="public",
                    text=turn.persona_output.public_response[:300],
                    annotation="Notable public response",
                )
            )
        if len(candidates) >= count:
            break

    return candidates[:count]


async def _generate_synthesis(
    turns: list[ConversationTurn],
    cooling_off: CoolingOff,
) -> str:
    """Call Haiku once to produce a 2-3 sentence synthesis paragraph."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY, max_retries=API_MAX_RETRIES)

    turn_summaries = []
    for turn in turns:
        po = turn.persona_output
        turn_summaries.append(
            f"Turn {turn.turn_number}: private stance {po.private_stance:.1f}, "
            f"emotion {po.emotional_reaction.primary_emotion.value}, "
            f'monologue excerpt: "{po.internal_monologue[:150]}"'
        )

    summary_text = "\n".join(turn_summaries)
    cooling_text = (
        f"Post-conversation reflection stance: {cooling_off.post_reflection_stance:.1f}. "
        f'Reflection: "{cooling_off.post_conversation_reflection[:200]}"'
    )

    system = (
        "You are an expert analyst of persuasion and attitude change. "
        "Write a 2-3 sentence synthesis paragraph describing how this conversation "
        "affected the participant's thinking. Be precise and analytical. "
        "Do not editorialize — describe what the data shows."
    )
    user = (
        f"Conversation summary:\n{summary_text}\n\n"
        f"Cooling-off turn:\n{cooling_text}\n\n"
        "Write a 2-3 sentence synthesis paragraph. Return only the paragraph text."
    )

    message = await client.messages.create(
        model=MODEL_ID,
        max_tokens=_SYNTHESIS_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text.strip()


async def score_conversation(
    turns: list[ConversationTurn],
    cooling_off: CoolingOff,
) -> tuple[CognitiveScores, list[StandoutQuote], str]:
    """
    Score a completed conversation across all cognitive dimensions.

    Runs 6 main-turn judge calls + 1 persistence call on cooling-off in parallel.
    Aggregates into CognitiveScores, selects standout quotes, and generates a
    synthesis paragraph.

    Returns:
        (CognitiveScores, standout_quotes, synthesis_paragraph)
    """
    transcript_text = _serialize_turns(turns)
    cooling_text = _serialize_cooling_off(cooling_off)
    full_transcript = transcript_text + "\n\nCooling-off turn:\n" + cooling_text

    async def _throttled_judge(prompt: str, transcript: str) -> dict:
        async with _JUDGE_SEMAPHORE:
            return await run_judge_call(prompt, transcript)

    # Run all 7 judge calls in parallel, capped at 4 concurrent connections
    (
        gap_result,
        threat_result,
        reasoning_result,
        engagement_result,
        ambivalence_result,
        residue_result,
        persistence_result,
    ) = await asyncio.gather(
        _throttled_judge(PUBLIC_PRIVATE_GAP_PROMPT, transcript_text),
        _throttled_judge(IDENTITY_THREAT_PROMPT, transcript_text),
        _throttled_judge(MOTIVATED_REASONING_PROMPT, transcript_text),
        _throttled_judge(ENGAGEMENT_DEPTH_PROMPT, transcript_text),
        _throttled_judge(AMBIVALENCE_PRESENCE_PROMPT, transcript_text),
        _throttled_judge(MEMORY_RESIDUE_PROMPT, transcript_text),
        _throttled_judge(PERSISTENCE_PROMPT, full_transcript),
    )

    # Count identity threats from the structured turn data (faster + more reliable
    # than inferring from judge score)
    identity_threats_triggered = sum(
        1 for turn in turns if turn.persona_output.identity_threat.threatened
    )

    # Count turns where memory_to_carry_forward is non-empty
    memory_residue_count = sum(
        1
        for turn in turns
        if turn.persona_output.memory_to_carry_forward.strip()
    )

    cognitive_scores = CognitiveScores(
        identity_threats_triggered=identity_threats_triggered,
        average_engagement_depth=engagement_result["score"],
        motivated_reasoning_intensity=reasoning_result["score"],
        ambivalence_presence=ambivalence_result["score"],
        memory_residue_count=memory_residue_count,
        public_private_gap_score=gap_result["score"],
        persistence=_persistence_from_score(persistence_result["score"]),
    )

    standout_quotes = _select_standout_quotes(turns)

    synthesis = await _generate_synthesis(turns, cooling_off)

    return cognitive_scores, standout_quotes, synthesis
