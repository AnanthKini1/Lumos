"""
Tests for validate_predictions.compute_validation_rate and helpers.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_predictions import (
    _classify_prediction,
    _is_match,
    compute_validation_rate,
)
from models import (
    CognitiveScores,
    CoolingOff,
    ConversationTurn,
    EmotionalReaction,
    IdentityThreat,
    PersonaProfile,
    PersonaTurnOutput,
    PersistenceResult,
    PrimaryEmotion,
    ResponseInclination,
    StrategyOutcome,
    Trajectory,
    VerdictCategory,
    CommunicationPreferences,
    EmotionalTriggers,
    SourceCitation,
    StandoutQuote,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_persona(
    persona_id: str,
    predictions: dict[str, str],
) -> PersonaProfile:
    return PersonaProfile(
        id=persona_id,
        display_name="Test Persona",
        demographic_shorthand="test",
        first_person_description="I am a test persona." * 20,
        core_values=["honesty", "fairness", "pragmatism"],
        communication_preferences=CommunicationPreferences(
            directness="direct",
            evidence_preference="data",
            tone="neutral",
        ),
        trust_orientation=["science"],
        identity_groups=["researchers"],
        emotional_triggers=EmotionalTriggers(
            defensive_when=["dismissed"],
            open_when=["respected"],
        ),
        trusted_sources=["peer-reviewed journals"],
        source_citation=SourceCitation(
            primary_source="test",
            url=None,
            supplementary=[],
        ),
        predicted_behavior_under_strategies=predictions,
    )


def _make_outcome(
    persona_id: str,
    strategy_id: str,
    verdict: VerdictCategory,
) -> StrategyOutcome:
    turn = ConversationTurn(
        turn_number=1,
        interviewer_message="hello",
        interviewer_strategy_note="note",
        persona_output=PersonaTurnOutput(
            internal_monologue="thinking",
            emotional_reaction=EmotionalReaction(
                primary_emotion=PrimaryEmotion.CURIOUS,
                intensity=5,
                trigger="argument",
            ),
            identity_threat=IdentityThreat(
                threatened=False,
                response_inclination=ResponseInclination.ACCEPT,
            ),
            private_stance=5.0,
            public_stance=5.0,
            private_stance_change_reason="",
            memory_to_carry_forward="",
            public_response="ok",
        ),
    )
    cooling_off = CoolingOff(post_conversation_reflection="ok", post_reflection_stance=5.0)
    trajectory = Trajectory(
        public_stance_per_turn=[5.0],
        private_stance_per_turn=[5.0],
        gap_per_turn=[0.0],
    )
    scores = CognitiveScores(
        identity_threats_triggered=0,
        average_engagement_depth=5.0,
        motivated_reasoning_intensity=3.0,
        ambivalence_presence=4.0,
        memory_residue_count=1,
        public_private_gap_score=1.0,
        persistence=PersistenceResult.HELD,
    )
    return StrategyOutcome(
        strategy_id=strategy_id,
        persona_id=persona_id,
        topic_id="topic_test",
        turns=[turn],
        cooling_off=cooling_off,
        trajectory=trajectory,
        cognitive_scores=scores,
        verdict=verdict,
        verdict_reasoning="test",
        standout_quotes=[],
        synthesis_paragraph="synthesis",
    )


# ---------------------------------------------------------------------------
# Tests — _classify_prediction
# ---------------------------------------------------------------------------

class TestClassifyPrediction:
    def test_positive_keywords(self) -> None:
        assert _classify_prediction("Expected to engage and be receptive") == "expected_positive"

    def test_defensive_keywords(self) -> None:
        assert _classify_prediction("Expected to be defensive and resist") == "expected_defensive"

    def test_neutral_keywords(self) -> None:
        assert _classify_prediction("Outcome is uncertain and mixed") == "expected_neutral"

    def test_empty_string(self) -> None:
        assert _classify_prediction("") == "expected_neutral"

    def test_dominant_positive_wins_over_tie(self) -> None:
        # More positive than defensive
        text = "Expected to engage, connect, and resonate rather than resist"
        result = _classify_prediction(text)
        assert result == "expected_positive"

    def test_dominant_defensive_wins(self) -> None:
        text = "Expected to be defensive, reject, and resist the argument"
        result = _classify_prediction(text)
        assert result == "expected_defensive"


# ---------------------------------------------------------------------------
# Tests — _is_match
# ---------------------------------------------------------------------------

class TestIsMatch:
    def test_neutral_always_matches(self) -> None:
        for verdict in VerdictCategory:
            assert _is_match("expected_neutral", verdict) is True

    def test_positive_matches_genuine_shift(self) -> None:
        assert _is_match("expected_positive", VerdictCategory.GENUINE_BELIEF_SHIFT)

    def test_positive_matches_partial_shift(self) -> None:
        assert _is_match("expected_positive", VerdictCategory.PARTIAL_SHIFT)

    def test_positive_does_not_match_backfire(self) -> None:
        assert not _is_match("expected_positive", VerdictCategory.BACKFIRE)

    def test_defensive_matches_backfire(self) -> None:
        assert _is_match("expected_defensive", VerdictCategory.BACKFIRE)

    def test_defensive_matches_no_movement(self) -> None:
        assert _is_match("expected_defensive", VerdictCategory.NO_MOVEMENT)

    def test_defensive_does_not_match_genuine_shift(self) -> None:
        assert not _is_match("expected_defensive", VerdictCategory.GENUINE_BELIEF_SHIFT)


# ---------------------------------------------------------------------------
# Tests — compute_validation_rate
# ---------------------------------------------------------------------------

class TestComputeValidationRate:
    def test_perfect_match_rate(self) -> None:
        persona = _make_persona("p1", {"s1": "Expected to engage and be receptive"})
        outcome = _make_outcome("p1", "s1", VerdictCategory.GENUINE_BELIEF_SHIFT)
        result = compute_validation_rate([outcome], {"p1": persona})
        assert result["match_rate"] == 1.0
        assert result["matched_pairs"] == 1
        assert result["total_pairs"] == 1

    def test_zero_match_rate(self) -> None:
        persona = _make_persona("p1", {"s1": "Expected to engage and be receptive"})
        outcome = _make_outcome("p1", "s1", VerdictCategory.BACKFIRE)
        result = compute_validation_rate([outcome], {"p1": persona})
        assert result["match_rate"] == 0.0

    def test_neutral_prediction_always_matches(self) -> None:
        persona = _make_persona("p1", {"s1": "Outcome uncertain, mixed signals expected"})
        outcome = _make_outcome("p1", "s1", VerdictCategory.BACKFIRE)
        result = compute_validation_rate([outcome], {"p1": persona})
        assert result["match_rate"] == 1.0

    def test_by_strategy_breakdown(self) -> None:
        persona = _make_persona(
            "p1",
            {
                "s1": "Expected to engage and be receptive",
                "s2": "Expected to be defensive and resist",
            },
        )
        outcomes = [
            _make_outcome("p1", "s1", VerdictCategory.GENUINE_BELIEF_SHIFT),  # match
            _make_outcome("p1", "s2", VerdictCategory.GENUINE_BELIEF_SHIFT),  # no match
        ]
        result = compute_validation_rate(outcomes, {"p1": persona})
        assert result["by_strategy"]["s1"] == 1.0
        assert result["by_strategy"]["s2"] == 0.0

    def test_by_persona_breakdown(self) -> None:
        p1 = _make_persona("p1", {"s1": "Expected to engage and be receptive"})
        p2 = _make_persona("p2", {"s1": "Expected to be defensive and resist"})
        outcomes = [
            _make_outcome("p1", "s1", VerdictCategory.GENUINE_BELIEF_SHIFT),  # match
            _make_outcome("p2", "s1", VerdictCategory.GENUINE_BELIEF_SHIFT),  # no match
        ]
        result = compute_validation_rate(outcomes, {"p1": p1, "p2": p2})
        assert result["by_persona"]["p1"] == 1.0
        assert result["by_persona"]["p2"] == 0.0

    def test_surprises_only_non_neutral_mismatches(self) -> None:
        persona = _make_persona(
            "p1",
            {
                "s1": "Expected to engage and be receptive",
                "s2": "Outcome uncertain",  # neutral
            },
        )
        outcomes = [
            _make_outcome("p1", "s1", VerdictCategory.BACKFIRE),  # non-neutral mismatch
            _make_outcome("p1", "s2", VerdictCategory.BACKFIRE),  # neutral — not a surprise
        ]
        result = compute_validation_rate(outcomes, {"p1": persona})
        assert len(result["surprises"]) == 1
        assert result["surprises"][0]["strategy_id"] == "s1"

    def test_missing_persona_skipped(self) -> None:
        outcome = _make_outcome("unknown_persona", "s1", VerdictCategory.PARTIAL_SHIFT)
        result = compute_validation_rate([outcome], {})
        assert result["total_pairs"] == 0

    def test_empty_outcomes(self) -> None:
        result = compute_validation_rate([], {})
        assert result["match_rate"] == 0.0
        assert result["total_pairs"] == 0
        assert result["surprises"] == []
