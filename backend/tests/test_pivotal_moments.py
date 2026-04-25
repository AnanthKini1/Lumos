"""
Tests for simulation.pipeline._annotate_pivotal_moments.

Pure Python — no mocks, no network. Covers:
- stance_delta is computed correctly from starting_stance and prior turn
- is_pivotal is True iff abs(delta) >= PIVOTAL_THRESHOLD (1.0)
- is_inflection_point marks exactly one turn — the one with the largest abs delta
- intensity is normalized 0-1, inflection point always has intensity == 1.0
- all turns (not just pivotal ones) get all fields set
- empty turn list returns immediately without error
- negative deltas (stance moves down) are handled correctly
- ties in delta magnitude — first occurrence wins for inflection point
- starting_stance is used as the baseline for turn 1's delta
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    ConversationTurn,
    EmotionalReaction,
    IdentityThreat,
    PersonaTurnOutput,
    PrimaryEmotion,
    ResponseInclination,
)
from simulation.pipeline import _PIVOTAL_THRESHOLD, _annotate_pivotal_moments


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_turn(turn_number: int, private_stance: float, public_stance: float = 5.0) -> ConversationTurn:
    return ConversationTurn(
        turn_number=turn_number,
        persuader_message="test message",
        persuader_strategy_note="note",
        persona_output=PersonaTurnOutput(
            internal_monologue="thinking",
            emotional_reaction=EmotionalReaction(
                primary_emotion=PrimaryEmotion.CURIOUS,
                intensity=5,
                trigger="argument",
            ),
            identity_threat=IdentityThreat(
                threatened=False,
                what_was_threatened=None,
                response_inclination=ResponseInclination.ACCEPT,
            ),
            private_stance=private_stance,
            public_stance=public_stance,
            private_stance_change_reason="because",
            memory_to_carry_forward="something",
            public_response="I see",
        ),
    )


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

class TestEmptyTurns:
    def test_empty_list_returns_empty_list(self) -> None:
        result = _annotate_pivotal_moments([], starting_stance=5.0)
        assert result == []

    def test_empty_list_does_not_raise(self) -> None:
        _annotate_pivotal_moments([], starting_stance=5.0)


# ---------------------------------------------------------------------------
# stance_delta computation
# ---------------------------------------------------------------------------

class TestStanceDelta:
    def test_first_turn_delta_uses_starting_stance(self) -> None:
        turns = [_make_turn(1, private_stance=6.5)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].stance_delta == pytest.approx(1.5)

    def test_second_turn_delta_uses_prior_turn_stance(self) -> None:
        turns = [_make_turn(1, private_stance=6.0), _make_turn(2, private_stance=7.5)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[1].stance_delta == pytest.approx(1.5)

    def test_negative_delta_when_stance_decreases(self) -> None:
        turns = [_make_turn(1, private_stance=4.0)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].stance_delta == pytest.approx(-1.0)

    def test_zero_delta_when_stance_unchanged(self) -> None:
        turns = [_make_turn(1, private_stance=5.0)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].stance_delta == pytest.approx(0.0)

    def test_all_turns_have_stance_delta_set(self) -> None:
        turns = [_make_turn(i, private_stance=5.0 + i * 0.3) for i in range(1, 7)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        for turn in turns:
            assert turn.stance_delta is not None


# ---------------------------------------------------------------------------
# is_pivotal
# ---------------------------------------------------------------------------

class TestIsPivotal:
    def test_delta_above_threshold_is_pivotal(self) -> None:
        turns = [_make_turn(1, private_stance=5.0 + _PIVOTAL_THRESHOLD + 0.1)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_pivotal is True

    def test_delta_exactly_at_threshold_is_pivotal(self) -> None:
        turns = [_make_turn(1, private_stance=5.0 + _PIVOTAL_THRESHOLD)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_pivotal is True

    def test_delta_below_threshold_is_not_pivotal(self) -> None:
        turns = [_make_turn(1, private_stance=5.0 + _PIVOTAL_THRESHOLD - 0.1)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_pivotal is False

    def test_negative_delta_above_threshold_is_pivotal(self) -> None:
        turns = [_make_turn(1, private_stance=5.0 - _PIVOTAL_THRESHOLD - 0.1)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_pivotal is True

    def test_zero_delta_is_not_pivotal(self) -> None:
        turns = [_make_turn(1, private_stance=5.0)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_pivotal is False

    def test_multiple_pivotal_turns_possible(self) -> None:
        turns = [
            _make_turn(1, private_stance=6.5),   # delta +1.5 → pivotal
            _make_turn(2, private_stance=5.0),   # delta -1.5 → pivotal
            _make_turn(3, private_stance=5.2),   # delta +0.2 → not pivotal
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_pivotal is True
        assert turns[1].is_pivotal is True
        assert turns[2].is_pivotal is False

    def test_no_pivotal_turns_when_all_small(self) -> None:
        turns = [_make_turn(i, private_stance=5.0 + i * 0.2) for i in range(1, 5)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert not any(t.is_pivotal for t in turns)


# ---------------------------------------------------------------------------
# is_inflection_point
# ---------------------------------------------------------------------------

class TestIsInflectionPoint:
    def test_exactly_one_inflection_point(self) -> None:
        turns = [
            _make_turn(1, private_stance=6.0),   # delta 1.0
            _make_turn(2, private_stance=8.5),   # delta 2.5 ← largest
            _make_turn(3, private_stance=8.8),   # delta 0.3
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        inflections = [t for t in turns if t.is_inflection_point]
        assert len(inflections) == 1

    def test_inflection_point_is_largest_delta_turn(self) -> None:
        turns = [
            _make_turn(1, private_stance=6.0),   # delta 1.0
            _make_turn(2, private_stance=8.5),   # delta 2.5 ← largest
            _make_turn(3, private_stance=8.8),   # delta 0.3
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[1].is_inflection_point is True

    def test_non_inflection_turns_are_false(self) -> None:
        turns = [
            _make_turn(1, private_stance=6.0),
            _make_turn(2, private_stance=8.5),
            _make_turn(3, private_stance=8.8),
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_inflection_point is False
        assert turns[2].is_inflection_point is False

    def test_single_turn_is_inflection_point(self) -> None:
        turns = [_make_turn(1, private_stance=6.5)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_inflection_point is True

    def test_tie_picks_first_occurrence(self) -> None:
        # Two turns with identical absolute delta — first wins
        turns = [
            _make_turn(1, private_stance=7.0),   # delta 2.0
            _make_turn(2, private_stance=5.0),   # delta 2.0 (tie)
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_inflection_point is True
        assert turns[1].is_inflection_point is False

    def test_inflection_point_need_not_be_pivotal(self) -> None:
        # All turns are below PIVOTAL_THRESHOLD, but one is still the inflection point
        turns = [
            _make_turn(1, private_stance=5.4),   # delta 0.4
            _make_turn(2, private_stance=5.7),   # delta 0.3
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].is_inflection_point is True  # largest even if not pivotal
        assert not any(t.is_pivotal for t in turns)


# ---------------------------------------------------------------------------
# intensity
# ---------------------------------------------------------------------------

class TestIntensity:
    def test_inflection_point_has_intensity_one(self) -> None:
        turns = [
            _make_turn(1, private_stance=6.5),   # delta 1.5 ← largest
            _make_turn(2, private_stance=6.8),   # delta 0.3
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].intensity == pytest.approx(1.0)

    def test_other_turns_have_intensity_less_than_one(self) -> None:
        turns = [
            _make_turn(1, private_stance=6.5),
            _make_turn(2, private_stance=6.8),
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[1].intensity < 1.0

    def test_intensity_is_proportional_to_delta(self) -> None:
        turns = [
            _make_turn(1, private_stance=7.0),   # delta 2.0
            _make_turn(2, private_stance=8.0),   # delta 1.0 → intensity = 0.5
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[1].intensity == pytest.approx(0.5)

    def test_all_turns_have_intensity_set(self) -> None:
        turns = [_make_turn(i, private_stance=5.0 + i * 0.5) for i in range(1, 5)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        for turn in turns:
            assert turn.intensity is not None

    def test_intensity_in_zero_to_one_range(self) -> None:
        turns = [_make_turn(i, private_stance=5.0 + i * 0.8) for i in range(1, 7)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        for turn in turns:
            assert 0.0 <= turn.intensity <= 1.0

    def test_zero_delta_turn_has_zero_intensity(self) -> None:
        turns = [
            _make_turn(1, private_stance=7.0),   # delta 2.0 ← largest
            _make_turn(2, private_stance=7.0),   # delta 0.0
        ]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[1].intensity == pytest.approx(0.0)

    def test_single_turn_intensity_is_one(self) -> None:
        turns = [_make_turn(1, private_stance=6.0)]
        _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert turns[0].intensity == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Return value and in-place mutation
# ---------------------------------------------------------------------------

class TestReturnBehavior:
    def test_returns_the_same_list(self) -> None:
        turns = [_make_turn(1, private_stance=6.5)]
        result = _annotate_pivotal_moments(turns, starting_stance=5.0)
        assert result is turns

    def test_modifies_turns_in_place(self) -> None:
        turn = _make_turn(1, private_stance=6.5)
        _annotate_pivotal_moments([turn], starting_stance=5.0)
        assert turn.stance_delta != 0.0  # was mutated
