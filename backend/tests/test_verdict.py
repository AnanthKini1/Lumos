"""
Tests for measurement.verdict.compute_verdict.

Pure Python — no mocks needed. Covers all 5 verdict categories and edge cases.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from measurement.verdict import (
    GENUINE_SHIFT_MAX_AVG_GAP,
    GENUINE_SHIFT_MIN_PRIVATE_DELTA,
    NO_MOVEMENT_MAX_DELTA,
    PARTIAL_SHIFT_MIN_PRIVATE_DELTA,
    SURFACE_COMPLIANCE_MAX_PRIVATE_DELTA,
    SURFACE_COMPLIANCE_MIN_PUBLIC_DELTA,
    compute_verdict,
)
from models import CognitiveScores, PersistenceResult, Trajectory, VerdictCategory


def _trajectory(
    private: list[float],
    public: list[float] | None = None,
) -> Trajectory:
    if public is None:
        public = private[:]
    gaps = [abs(pub - priv) for pub, priv in zip(public, private)]
    return Trajectory(
        public_stance_per_turn=public,
        private_stance_per_turn=private,
        gap_per_turn=gaps,
    )


def _scores(
    *,
    gap_score: float = 1.0,
    persistence: PersistenceResult = PersistenceResult.HELD,
) -> CognitiveScores:
    return CognitiveScores(
        identity_threats_triggered=0,
        average_engagement_depth=5.0,
        motivated_reasoning_intensity=3.0,
        ambivalence_presence=4.0,
        memory_residue_count=1,
        public_private_gap_score=gap_score,
        persistence=persistence,
    )


class TestGenuineBeliefShift:
    def test_large_private_delta_low_gap_held(self) -> None:
        traj = _trajectory(private=[3.0, 5.5, 6.0], public=[3.0, 5.5, 6.0])
        verdict, reason = compute_verdict(traj, _scores(gap_score=1.0), starting_stance=3.0)
        assert verdict == VerdictCategory.GENUINE_BELIEF_SHIFT
        assert "GENUINE_BELIEF_SHIFT" not in reason  # reason is English, not enum name
        assert "+3.0" in reason or "3.0" in reason

    def test_partially_reverted_still_qualifies(self) -> None:
        traj = _trajectory(private=[3.0, 5.5, 6.0])
        verdict, _ = compute_verdict(
            traj,
            _scores(gap_score=1.0, persistence=PersistenceResult.PARTIALLY_REVERTED),
            starting_stance=3.0,
        )
        assert verdict == VerdictCategory.GENUINE_BELIEF_SHIFT

    def test_fully_reverted_does_not_qualify(self) -> None:
        traj = _trajectory(private=[3.0, 5.5, 6.0])
        verdict, _ = compute_verdict(
            traj,
            _scores(gap_score=1.0, persistence=PersistenceResult.FULLY_REVERTED),
            starting_stance=3.0,
        )
        assert verdict != VerdictCategory.GENUINE_BELIEF_SHIFT

    def test_high_gap_disqualifies(self) -> None:
        traj = _trajectory(private=[3.0, 5.5, 6.0])
        verdict, _ = compute_verdict(
            traj,
            _scores(gap_score=GENUINE_SHIFT_MAX_AVG_GAP + 0.1),
            starting_stance=3.0,
        )
        assert verdict != VerdictCategory.GENUINE_BELIEF_SHIFT


class TestPartialShift:
    def test_private_delta_in_partial_range(self) -> None:
        traj = _trajectory(private=[4.0, 4.5, 5.3])
        verdict, reason = compute_verdict(traj, _scores(gap_score=1.0), starting_stance=4.0)
        assert verdict == VerdictCategory.PARTIAL_SHIFT
        assert "partial" in reason.lower()

    def test_at_exact_partial_threshold(self) -> None:
        # delta == PARTIAL_SHIFT_MIN_PRIVATE_DELTA exactly
        traj = _trajectory(private=[5.0, 6.0])
        verdict, _ = compute_verdict(traj, _scores(gap_score=4.0), starting_stance=5.0)
        assert verdict == VerdictCategory.PARTIAL_SHIFT

    def test_genuine_shift_threshold_not_partial(self) -> None:
        # delta == GENUINE_SHIFT_MIN_PRIVATE_DELTA with good gap and persistence
        traj = _trajectory(private=[3.0, 5.0])
        verdict, _ = compute_verdict(traj, _scores(gap_score=1.0), starting_stance=3.0)
        assert verdict == VerdictCategory.GENUINE_BELIEF_SHIFT


class TestSurfaceCompliance:
    def test_public_moves_private_does_not(self) -> None:
        traj = _trajectory(
            private=[5.0, 5.2, 5.4],
            public=[5.0, 6.5, 7.5],
        )
        verdict, reason = compute_verdict(traj, _scores(gap_score=3.0), starting_stance=5.0)
        assert verdict == VerdictCategory.SURFACE_COMPLIANCE
        assert "public" in reason.lower()

    def test_both_move_significantly_not_surface(self) -> None:
        traj = _trajectory(
            private=[3.0, 5.5, 6.0],
            public=[3.0, 6.0, 6.5],
        )
        verdict, _ = compute_verdict(traj, _scores(gap_score=0.5), starting_stance=3.0)
        assert verdict == VerdictCategory.GENUINE_BELIEF_SHIFT


class TestBackfire:
    def test_private_moves_opposite_to_public(self) -> None:
        # public moves up, private moves down significantly
        traj = _trajectory(
            private=[5.0, 4.0, 3.5],
            public=[5.0, 6.5, 7.5],
        )
        verdict, reason = compute_verdict(traj, _scores(gap_score=4.0), starting_stance=5.0)
        assert verdict == VerdictCategory.BACKFIRE
        assert "opposite" in reason.lower() or "backfire" in reason.lower()

    def test_private_and_public_same_direction_not_backfire(self) -> None:
        traj = _trajectory(private=[3.0, 4.5, 5.5], public=[3.0, 5.0, 5.5])
        verdict, _ = compute_verdict(traj, _scores(gap_score=0.5), starting_stance=3.0)
        assert verdict != VerdictCategory.BACKFIRE


class TestNoMovement:
    def test_tiny_private_and_public_delta(self) -> None:
        traj = _trajectory(private=[5.0, 5.3, 5.5], public=[5.0, 5.4, 5.6])
        verdict, reason = compute_verdict(traj, _scores(gap_score=0.5), starting_stance=5.0)
        assert verdict == VerdictCategory.NO_MOVEMENT

    def test_empty_trajectory(self) -> None:
        traj = Trajectory(public_stance_per_turn=[], private_stance_per_turn=[], gap_per_turn=[])
        verdict, _ = compute_verdict(traj, _scores(), starting_stance=5.0)
        assert verdict == VerdictCategory.NO_MOVEMENT


class TestReasoningStrings:
    def test_returns_non_empty_reasoning(self) -> None:
        traj = _trajectory(private=[5.0, 5.5])
        _, reason = compute_verdict(traj, _scores(), starting_stance=5.0)
        assert reason.strip()

    def test_reasoning_is_string(self) -> None:
        traj = _trajectory(private=[3.0, 5.5, 6.5])
        _, reason = compute_verdict(traj, _scores(gap_score=1.0), starting_stance=3.0)
        assert isinstance(reason, str)
