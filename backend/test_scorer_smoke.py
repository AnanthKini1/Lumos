"""
A5.11 — Smoke test for score_conversation.

Loads mock_simulation.json, runs score_conversation on the first outcome's
turns + cooling_off, and verifies the result structure. All LLM calls are
mocked — this tests integration of scorer + verdict + data parsing, not
network connectivity.

Run with:
    python backend/test_scorer_smoke.py
or:
    python -m pytest backend/test_scorer_smoke.py -v
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))

from measurement.scorer import score_conversation
from measurement.verdict import compute_verdict
from models import (
    CognitiveScores,
    ConversationTurn,
    CoolingOff,
    PersistenceResult,
    StandoutQuote,
    Trajectory,
)

MOCK_SIMULATION_PATH = (
    Path(__file__).parent.parent / "frontend" / "src" / "data" / "mock_simulation.json"
)


def load_first_outcome() -> tuple[list[ConversationTurn], CoolingOff]:
    """Load turns and cooling_off from the first outcome in mock_simulation.json."""
    data = json.loads(MOCK_SIMULATION_PATH.read_text(encoding="utf-8"))
    outcome = data["outcomes"][0]
    turns = [ConversationTurn.model_validate(t) for t in outcome["turns"]]
    cooling_off = CoolingOff.model_validate(outcome["cooling_off"])
    return turns, cooling_off


def _make_judge_result(score: float) -> dict:
    return {"score": score, "evidence_quotes": ["quote 1", "quote 2"]}


async def run_smoke_test() -> None:
    print(f"Loading mock simulation from: {MOCK_SIMULATION_PATH}")
    turns, cooling_off = load_first_outcome()
    print(f"Loaded {len(turns)} turns + cooling_off (stance: {cooling_off.post_reflection_stance})")

    # Mock all LLM calls with reasonable scores
    judge_results = [
        _make_judge_result(2.5),   # gap
        _make_judge_result(7.0),   # threat
        _make_judge_result(3.5),   # reasoning
        _make_judge_result(8.0),   # engagement
        _make_judge_result(6.0),   # ambivalence
        _make_judge_result(7.5),   # residue
        _make_judge_result(7.0),   # persistence -> HELD
    ]
    call_count = {"n": 0}

    async def _fake_judge(prompt, transcript):
        result = judge_results[call_count["n"]]
        call_count["n"] += 1
        return result

    synthesis_content = MagicMock()
    synthesis_content.text = (
        "The participant began with a strong pro-RTO stance and showed genuine engagement "
        "with the personal narrative. By the third turn, private belief had shifted "
        "measurably, and the cooling-off reflection confirmed partial persistence of the change."
    )
    synthesis_message = MagicMock()
    synthesis_message.content = [synthesis_content]

    with patch("measurement.scorer.run_judge_call", side_effect=_fake_judge):
        with patch("measurement.scorer.anthropic.AsyncAnthropic") as mock_cls:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=synthesis_message)
            mock_cls.return_value = mock_client

            scores, quotes, synthesis = await score_conversation(turns, cooling_off)

    # --- Verify CognitiveScores ---
    assert isinstance(scores, CognitiveScores), f"Expected CognitiveScores, got {type(scores)}"
    assert 0.0 <= scores.average_engagement_depth <= 10.0
    assert 0.0 <= scores.motivated_reasoning_intensity <= 10.0
    assert 0.0 <= scores.ambivalence_presence <= 10.0
    assert 0.0 <= scores.public_private_gap_score <= 10.0
    assert scores.identity_threats_triggered >= 0
    assert scores.memory_residue_count >= 0
    assert isinstance(scores.persistence, PersistenceResult)
    print(f"\nCognitiveScores:")
    print(f"  engagement_depth:          {scores.average_engagement_depth}")
    print(f"  motivated_reasoning:       {scores.motivated_reasoning_intensity}")
    print(f"  ambivalence_presence:      {scores.ambivalence_presence}")
    print(f"  public_private_gap_score:  {scores.public_private_gap_score}")
    print(f"  identity_threats:          {scores.identity_threats_triggered}")
    print(f"  memory_residue_count:      {scores.memory_residue_count}")
    print(f"  persistence:               {scores.persistence.value}")

    # --- Verify StandoutQuotes ---
    assert isinstance(quotes, list), f"Expected list, got {type(quotes)}"
    assert len(quotes) > 0, "Expected at least one standout quote"
    assert all(isinstance(q, StandoutQuote) for q in quotes)
    print(f"\nStandout Quotes ({len(quotes)}):")
    for q in quotes:
        print(f"  [turn {q.turn}] [{q.type}] {q.text[:80]}...")

    # --- Verify synthesis ---
    assert isinstance(synthesis, str), f"Expected str, got {type(synthesis)}"
    assert synthesis.strip(), "synthesis_paragraph must not be empty"
    print(f"\nSynthesis paragraph:\n  {synthesis[:200]}...")

    # --- Run compute_verdict on trajectory from the outcome ---
    data = json.loads(MOCK_SIMULATION_PATH.read_text(encoding="utf-8"))
    outcome = data["outcomes"][0]
    trajectory = Trajectory.model_validate(outcome["trajectory"])
    starting_stance = data["metadata"]["topic"]["predicted_starting_stances"].get(
        outcome["persona_id"], 5.0
    )
    verdict, reasoning = compute_verdict(trajectory, scores, starting_stance)
    print(f"\nVerdict: {verdict.value}")
    print(f"Reasoning: {reasoning}")

    print("\n--- SMOKE TEST PASSED ---")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
