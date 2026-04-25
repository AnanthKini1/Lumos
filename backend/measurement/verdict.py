"""
WS-A — Verdict logic. Pure function, no LLM calls, no I/O.

Takes raw trajectory data and cognitive scores and returns a categorical verdict
plus a short rule-based explanation. The rules are deterministic and transparent
so they can be cited in the pitch.

Verdict categories and their rules:
  GENUINE_BELIEF_SHIFT  — private stance moved >2.0, public-private gap <1.5 avg,
                          change persisted under cooling-off (held or partial)
  PARTIAL_SHIFT         — private stance moved 1.0-2.0, or held but gap was wide
  SURFACE_COMPLIANCE    — public stance moved >2.0 but private stance moved <1.0
  BACKFIRE              — private stance moved opposite the intended direction
  NO_MOVEMENT           — neither public nor private stance moved >1.0

All thresholds are defined as named constants here so they appear in one place
and can be adjusted without hunting through logic.
"""

from models import CognitiveScores, PersistenceResult, Trajectory, VerdictCategory

# ---------------------------------------------------------------------------
# Thresholds (adjust here only — never hard-code in logic below)
# ---------------------------------------------------------------------------

GENUINE_SHIFT_MIN_PRIVATE_DELTA: float = 2.0
GENUINE_SHIFT_MAX_AVG_GAP: float = 1.5
PARTIAL_SHIFT_MIN_PRIVATE_DELTA: float = 1.0
SURFACE_COMPLIANCE_MIN_PUBLIC_DELTA: float = 2.0
SURFACE_COMPLIANCE_MAX_PRIVATE_DELTA: float = 1.0
NO_MOVEMENT_MAX_DELTA: float = 1.0


def compute_verdict(
    trajectory: Trajectory,
    cognitive_scores: CognitiveScores,
    starting_stance: float,
) -> tuple[VerdictCategory, str]:
    """
    Deterministic verdict computation from trajectory + cognitive scores.

    Returns:
        (VerdictCategory, verdict_reasoning_string)
    """
    raise NotImplementedError
