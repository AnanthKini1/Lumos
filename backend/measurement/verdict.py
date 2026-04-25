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

    Evaluation order matters — checks are applied from most specific to most
    general. The first matching rule wins.

    Returns:
        (VerdictCategory, verdict_reasoning_string)
    """
    if not trajectory.private_stance_per_turn:
        return (
            VerdictCategory.NO_MOVEMENT,
            "No turns recorded — cannot assess movement.",
        )

    final_private = trajectory.private_stance_per_turn[-1]
    final_public = trajectory.public_stance_per_turn[-1] if trajectory.public_stance_per_turn else starting_stance

    private_delta = final_private - starting_stance
    public_delta = final_public - starting_stance
    avg_gap = cognitive_scores.public_private_gap_score
    persistence = cognitive_scores.persistence

    # BACKFIRE: private stance moved meaningfully in the wrong direction.
    # "Wrong direction" = moved away from neutral (toward more extreme opposition)
    # We detect this as a significant move opposite to public delta, or simply
    # any significant negative delta when the topic is being argued positively.
    # The simplest defensible rule: private moved by >= PARTIAL threshold in the
    # direction opposite to whatever public movement occurred.
    if public_delta != 0 and abs(private_delta) >= PARTIAL_SHIFT_MIN_PRIVATE_DELTA:
        if (private_delta > 0) != (public_delta > 0):
            return (
                VerdictCategory.BACKFIRE,
                (
                    f"Private stance moved {private_delta:+.1f} while public moved "
                    f"{public_delta:+.1f} — opposite directions indicate backfire effect."
                ),
            )

    # GENUINE_BELIEF_SHIFT: large private move, low gap, held through cooling-off.
    if (
        abs(private_delta) >= GENUINE_SHIFT_MIN_PRIVATE_DELTA
        and avg_gap <= GENUINE_SHIFT_MAX_AVG_GAP
        and persistence in (PersistenceResult.HELD, PersistenceResult.PARTIALLY_REVERTED)
    ):
        return (
            VerdictCategory.GENUINE_BELIEF_SHIFT,
            (
                f"Private stance shifted {private_delta:+.1f} points (threshold: "
                f"{GENUINE_SHIFT_MIN_PRIVATE_DELTA}), average public-private gap "
                f"{avg_gap:.1f} (threshold: ≤{GENUINE_SHIFT_MAX_AVG_GAP}), "
                f"and persistence: {persistence.value}."
            ),
        )

    # SURFACE_COMPLIANCE: public moved substantially but private barely moved.
    if (
        abs(public_delta) >= SURFACE_COMPLIANCE_MIN_PUBLIC_DELTA
        and abs(private_delta) < SURFACE_COMPLIANCE_MAX_PRIVATE_DELTA
    ):
        return (
            VerdictCategory.SURFACE_COMPLIANCE,
            (
                f"Public stance moved {public_delta:+.1f} (threshold: "
                f"≥{SURFACE_COMPLIANCE_MIN_PUBLIC_DELTA}) while private stance moved "
                f"only {private_delta:+.1f} (threshold: <{SURFACE_COMPLIANCE_MAX_PRIVATE_DELTA}) "
                f"— public agreement without private conviction."
            ),
        )

    # PARTIAL_SHIFT: meaningful private movement, but below genuine shift threshold.
    if abs(private_delta) >= PARTIAL_SHIFT_MIN_PRIVATE_DELTA:
        return (
            VerdictCategory.PARTIAL_SHIFT,
            (
                f"Private stance shifted {private_delta:+.1f} points — above the partial "
                f"shift threshold ({PARTIAL_SHIFT_MIN_PRIVATE_DELTA}) but below genuine "
                f"shift threshold ({GENUINE_SHIFT_MIN_PRIVATE_DELTA}). "
                f"Persistence: {persistence.value}."
            ),
        )

    # NO_MOVEMENT: neither public nor private moved meaningfully.
    return (
        VerdictCategory.NO_MOVEMENT,
        (
            f"Private stance moved only {private_delta:+.1f} and public stance moved "
            f"{public_delta:+.1f} — both below the no-movement threshold "
            f"({NO_MOVEMENT_MAX_DELTA})."
        ),
    )
