"""
Tests for measurement.scorer.score_conversation.

All LLM calls are mocked — no network traffic. Verifies aggregation logic,
standout quote selection, persistence mapping, and return types.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from measurement.scorer import (
    _persistence_from_score,
    _select_standout_quotes,
    score_conversation,
)
from models import (
    CognitiveScores,
    ConversationTurn,
    CoolingOff,
    EmotionalReaction,
    IdentityThreat,
    PersonaTurnOutput,
    PersistenceResult,
    PrimaryEmotion,
    ResponseInclination,
    StandoutQuote,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_turn(
    turn_number: int,
    private_stance: float = 5.0,
    emotion: PrimaryEmotion = PrimaryEmotion.CURIOUS,
    intensity: int = 5,
    threatened: bool = False,
    monologue: str = "I am thinking about this.",
    public_response: str = "That is interesting.",
    memory: str = "",
) -> ConversationTurn:
    return ConversationTurn(
        turn_number=turn_number,
        interviewer_message="What do you think?",
        interviewer_strategy_note="strategy note",
        persona_output=PersonaTurnOutput(
            internal_monologue=monologue,
            emotional_reaction=EmotionalReaction(
                primary_emotion=emotion,
                intensity=intensity,
                trigger="argument",
            ),
            identity_threat=IdentityThreat(
                threatened=threatened,
                what_was_threatened="values" if threatened else None,
                response_inclination=ResponseInclination.DEFEND if threatened else ResponseInclination.ACCEPT,
            ),
            private_stance=private_stance,
            public_stance=private_stance,
            private_stance_change_reason="",
            memory_to_carry_forward=memory,
            public_response=public_response,
        ),
    )


def _make_cooling_off(stance: float = 5.0) -> CoolingOff:
    return CoolingOff(
        post_conversation_reflection="I reflected on the conversation.",
        post_reflection_stance=stance,
    )


def _make_judge_result(score: float) -> dict:
    return {"score": score, "evidence_quotes": ["quote A", "quote B"]}


# ---------------------------------------------------------------------------
# Unit tests — persistence mapping
# ---------------------------------------------------------------------------

class TestPersistenceFromScore:
    def test_high_score_maps_to_held(self) -> None:
        assert _persistence_from_score(8.0) == PersistenceResult.HELD

    def test_boundary_held(self) -> None:
        assert _persistence_from_score(6.0) == PersistenceResult.HELD

    def test_mid_score_maps_to_partially_reverted(self) -> None:
        assert _persistence_from_score(4.5) == PersistenceResult.PARTIALLY_REVERTED

    def test_boundary_partially_reverted(self) -> None:
        assert _persistence_from_score(3.0) == PersistenceResult.PARTIALLY_REVERTED

    def test_low_score_maps_to_fully_reverted(self) -> None:
        assert _persistence_from_score(1.0) == PersistenceResult.FULLY_REVERTED

    def test_zero_maps_to_fully_reverted(self) -> None:
        assert _persistence_from_score(0.0) == PersistenceResult.FULLY_REVERTED


# ---------------------------------------------------------------------------
# Unit tests — standout quote selection
# ---------------------------------------------------------------------------

class TestSelectStandoutQuotes:
    def test_prefers_threatened_turns(self) -> None:
        turns = [
            _make_turn(1, threatened=False),
            _make_turn(2, threatened=True, monologue="Identity under attack here."),
            _make_turn(3, threatened=False),
        ]
        quotes = _select_standout_quotes(turns, count=1)
        assert quotes[0].turn == 2

    def test_prefers_high_intensity(self) -> None:
        turns = [
            _make_turn(1, intensity=3),
            _make_turn(2, intensity=9, monologue="Very emotional response."),
            _make_turn(3, intensity=2),
        ]
        quotes = _select_standout_quotes(turns, count=1)
        assert quotes[0].turn == 2

    def test_falls_back_to_public_response(self) -> None:
        turns = [_make_turn(i) for i in range(1, 4)]
        quotes = _select_standout_quotes(turns, count=3)
        assert len(quotes) == 3

    def test_returns_at_most_count(self) -> None:
        turns = [_make_turn(i, threatened=True) for i in range(1, 6)]
        quotes = _select_standout_quotes(turns, count=2)
        assert len(quotes) == 2

    def test_quote_text_truncated(self) -> None:
        long_text = "x" * 500
        turns = [_make_turn(1, monologue=long_text, threatened=True)]
        quotes = _select_standout_quotes(turns, count=1)
        assert len(quotes[0].text) <= 300


# ---------------------------------------------------------------------------
# Integration tests — score_conversation (mocked LLM calls)
# ---------------------------------------------------------------------------

MOCK_JUDGE_SCORES = {
    "gap": 3.0,
    "threat": 6.0,
    "reasoning": 4.0,
    "engagement": 7.0,
    "ambivalence": 5.0,
    "residue": 6.0,
    "persistence": 7.5,  # -> HELD
}


@pytest.fixture()
def mock_judge_and_synthesis():
    """Patch run_judge_call and the synthesis Anthropic client."""
    judge_results = [
        _make_judge_result(MOCK_JUDGE_SCORES["gap"]),
        _make_judge_result(MOCK_JUDGE_SCORES["threat"]),
        _make_judge_result(MOCK_JUDGE_SCORES["reasoning"]),
        _make_judge_result(MOCK_JUDGE_SCORES["engagement"]),
        _make_judge_result(MOCK_JUDGE_SCORES["ambivalence"]),
        _make_judge_result(MOCK_JUDGE_SCORES["residue"]),
        _make_judge_result(MOCK_JUDGE_SCORES["persistence"]),
    ]
    call_count = {"n": 0}

    async def _fake_judge(prompt, transcript):
        result = judge_results[call_count["n"]]
        call_count["n"] += 1
        return result

    synthesis_content = MagicMock()
    synthesis_content.text = "This is a synthesis paragraph."
    synthesis_message = MagicMock()
    synthesis_message.content = [synthesis_content]

    with patch("measurement.scorer.run_judge_call", side_effect=_fake_judge):
        with patch("measurement.scorer.anthropic.AsyncAnthropic") as mock_cls:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=synthesis_message)
            mock_cls.return_value = mock_client
            yield


class TestScoreConversation:
    async def test_returns_three_tuple(self, mock_judge_and_synthesis) -> None:
        turns = [_make_turn(i) for i in range(1, 4)]
        result = await score_conversation(turns, _make_cooling_off())
        assert len(result) == 3

    async def test_cognitive_scores_type(self, mock_judge_and_synthesis) -> None:
        turns = [_make_turn(i) for i in range(1, 4)]
        scores, _, _ = await score_conversation(turns, _make_cooling_off())
        assert isinstance(scores, CognitiveScores)

    async def test_engagement_depth_mapped_from_judge(self, mock_judge_and_synthesis) -> None:
        turns = [_make_turn(i) for i in range(1, 4)]
        scores, _, _ = await score_conversation(turns, _make_cooling_off())
        assert scores.average_engagement_depth == MOCK_JUDGE_SCORES["engagement"]

    async def test_persistence_mapped_from_score(self, mock_judge_and_synthesis) -> None:
        turns = [_make_turn(i) for i in range(1, 4)]
        scores, _, _ = await score_conversation(turns, _make_cooling_off())
        assert scores.persistence == PersistenceResult.HELD

    async def test_identity_threats_counted_from_turns(self, mock_judge_and_synthesis) -> None:
        turns = [
            _make_turn(1, threatened=True),
            _make_turn(2, threatened=False),
            _make_turn(3, threatened=True),
        ]
        scores, _, _ = await score_conversation(turns, _make_cooling_off())
        assert scores.identity_threats_triggered == 2

    async def test_memory_residue_counted_from_turns(self, mock_judge_and_synthesis) -> None:
        turns = [
            _make_turn(1, memory="I'll think about this."),
            _make_turn(2, memory=""),
            _make_turn(3, memory="The Iceland data stuck with me."),
        ]
        scores, _, _ = await score_conversation(turns, _make_cooling_off())
        assert scores.memory_residue_count == 2

    async def test_standout_quotes_list(self, mock_judge_and_synthesis) -> None:
        turns = [_make_turn(i) for i in range(1, 4)]
        _, quotes, _ = await score_conversation(turns, _make_cooling_off())
        assert isinstance(quotes, list)
        assert all(isinstance(q, StandoutQuote) for q in quotes)

    async def test_synthesis_is_non_empty_string(self, mock_judge_and_synthesis) -> None:
        turns = [_make_turn(i) for i in range(1, 4)]
        _, _, synthesis = await score_conversation(turns, _make_cooling_off())
        assert isinstance(synthesis, str)
        assert synthesis.strip()
