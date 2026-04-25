"""
A6.1 — Validation rate computation.

Compares actual simulation verdicts to the free-text predictions in each
persona's `predicted_behavior_under_strategies` field.

Classification rules (applied to prediction text, case-insensitive):
  - "expected_positive"  → actual verdict should be GENUINE_BELIEF_SHIFT or PARTIAL_SHIFT
  - "expected_defensive" → actual verdict should be BACKFIRE or NO_MOVEMENT
  - "expected_neutral"   → any verdict counts as a match

Prediction text is classified by scanning for keyword signals:
  Positive signals:  engage, open, receptive, shift, update, persuade, effective,
                     connect, resonate, movement, genuine, positive, partial
  Defensive signals: defensive, backfire, resist, reject, entrench, close, threaten,
                     ineffective, reactance, dismiss, hostile, harden
  Neutral signals:   neutral, mixed, uncertain, unclear, depends, vary, context

Usage:
    from validate_predictions import compute_validation_rate
    result = compute_validation_rate(outcomes, personas, strategies)

or from the command line:
    python backend/validate_predictions.py --input backend/output/simulations/my_run.json
    python backend/validate_predictions.py --mock   # run on mock_simulation.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TypedDict

from data.loader import load_persona
from models import PersonaProfile, StrategyOutcome, VerdictCategory

# ---------------------------------------------------------------------------
# Keyword sets for prediction classification
# ---------------------------------------------------------------------------

_POSITIVE_KEYWORDS = {
    "engage", "open", "receptive", "shift", "update", "persuade", "persuaded",
    "effective", "connect", "resonate", "movement", "genuine", "positive",
    "partial", "curious", "listen", "trust", "warm", "interested",
}

_DEFENSIVE_KEYWORDS = {
    "defensive", "backfire", "resist", "reject", "entrench", "close",
    "threaten", "ineffective", "reactance", "dismiss", "hostile", "harden",
    "dig in", "pushback", "backlash", "skeptic", "suspicious", "distrust",
}

_NEUTRAL_KEYWORDS = {
    "neutral", "mixed", "uncertain", "unclear", "depends", "vary",
    "context", "unpredictable", "ambivalent",
}

_POSITIVE_VERDICTS = {VerdictCategory.GENUINE_BELIEF_SHIFT, VerdictCategory.PARTIAL_SHIFT}
_DEFENSIVE_VERDICTS = {VerdictCategory.BACKFIRE, VerdictCategory.NO_MOVEMENT}


class PredictionMatch(TypedDict):
    persona_id: str
    strategy_id: str
    prediction_text: str
    predicted_class: str  # "expected_positive" | "expected_defensive" | "expected_neutral"
    actual_verdict: str
    matched: bool


class ValidationResult(TypedDict):
    match_rate: float
    by_strategy: dict[str, float]
    by_persona: dict[str, float]
    surprises: list[PredictionMatch]
    total_pairs: int
    matched_pairs: int


def _classify_prediction(text: str) -> str:
    """
    Classify a free-text prediction as expected_positive, expected_defensive,
    or expected_neutral using keyword scanning.

    When signals conflict, whichever type has more matching keywords wins.
    Ties or no signals → expected_neutral.
    """
    import re
    words = set(re.findall(r"[a-z]+", text.lower()))

    positive_hits = len(words & _POSITIVE_KEYWORDS)
    defensive_hits = len(words & _DEFENSIVE_KEYWORDS)
    neutral_hits = len(words & _NEUTRAL_KEYWORDS)

    if positive_hits == 0 and defensive_hits == 0 and neutral_hits == 0:
        return "expected_neutral"

    if positive_hits > defensive_hits and positive_hits > neutral_hits:
        return "expected_positive"
    if defensive_hits > positive_hits and defensive_hits > neutral_hits:
        return "expected_defensive"
    return "expected_neutral"


def _is_match(predicted_class: str, actual_verdict: VerdictCategory) -> bool:
    """Return True if actual verdict satisfies the prediction class."""
    if predicted_class == "expected_neutral":
        return True
    if predicted_class == "expected_positive":
        return actual_verdict in _POSITIVE_VERDICTS
    if predicted_class == "expected_defensive":
        return actual_verdict in _DEFENSIVE_VERDICTS
    return True


def compute_validation_rate(
    outcomes: list[StrategyOutcome],
    personas: dict[str, PersonaProfile],
) -> ValidationResult:
    """
    Compare actual verdicts to predicted behavior for every (persona, strategy) pair.

    Args:
        outcomes: List of StrategyOutcome from a simulation run.
        personas:  Dict mapping persona_id -> PersonaProfile (loaded from data/).

    Returns:
        ValidationResult with overall match_rate, per-strategy and per-persona
        breakdowns, and a list of surprise cases (predicted one direction, got another).
    """
    pairs: list[PredictionMatch] = []

    for outcome in outcomes:
        persona_id = outcome.persona_id
        strategy_id = outcome.strategy_id
        actual_verdict = outcome.verdict

        persona = personas.get(persona_id)
        if persona is None:
            continue  # persona data unavailable — skip

        prediction_text = persona.predicted_behavior_under_strategies.get(strategy_id, "")
        predicted_class = _classify_prediction(prediction_text)
        matched = _is_match(predicted_class, actual_verdict)

        pairs.append(
            PredictionMatch(
                persona_id=persona_id,
                strategy_id=strategy_id,
                prediction_text=prediction_text,
                predicted_class=predicted_class,
                actual_verdict=actual_verdict.value,
                matched=matched,
            )
        )

    total = len(pairs)
    matched_total = sum(1 for p in pairs if p["matched"])
    match_rate = matched_total / total if total > 0 else 0.0

    # Per-strategy breakdown
    by_strategy: dict[str, list[bool]] = {}
    for p in pairs:
        by_strategy.setdefault(p["strategy_id"], []).append(p["matched"])
    strategy_rates = {
        sid: sum(results) / len(results)
        for sid, results in by_strategy.items()
    }

    # Per-persona breakdown
    by_persona: dict[str, list[bool]] = {}
    for p in pairs:
        by_persona.setdefault(p["persona_id"], []).append(p["matched"])
    persona_rates = {
        pid: sum(results) / len(results)
        for pid, results in by_persona.items()
    }

    # Surprises: cases where prediction was non-neutral and was wrong
    surprises = [
        p for p in pairs
        if not p["matched"] and p["predicted_class"] != "expected_neutral"
    ]

    return ValidationResult(
        match_rate=round(match_rate, 3),
        by_strategy=strategy_rates,
        by_persona=persona_rates,
        surprises=surprises,
        total_pairs=total,
        matched_pairs=matched_total,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_outcomes_from_file(path: Path) -> list[StrategyOutcome]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_outcomes = data.get("outcomes", data) if isinstance(data, dict) else data
    return [StrategyOutcome.model_validate(o) for o in raw_outcomes]


def _load_all_personas_from_outcomes(outcomes: list[StrategyOutcome]) -> dict[str, PersonaProfile]:
    personas: dict[str, PersonaProfile] = {}
    for outcome in outcomes:
        pid = outcome.persona_id
        if pid not in personas:
            try:
                personas[pid] = load_persona(pid)
            except FileNotFoundError:
                pass
    return personas


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute prediction validation rate.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path, help="Path to simulation output JSON.")
    group.add_argument("--mock", action="store_true", help="Run on mock_simulation.json.")
    args = parser.parse_args()

    if args.mock:
        mock_path = Path(__file__).parent.parent / "frontend" / "src" / "data" / "mock_simulation.json"
        input_path = mock_path
    else:
        input_path = args.input

    print(f"Loading outcomes from: {input_path}")
    outcomes = _load_outcomes_from_file(input_path)
    print(f"Loaded {len(outcomes)} outcomes.")

    personas = _load_all_personas_from_outcomes(outcomes)
    print(f"Loaded {len(personas)} persona(s).")

    result = compute_validation_rate(outcomes, personas)

    print(f"\nMatch rate: {result['match_rate']:.1%} ({result['matched_pairs']}/{result['total_pairs']})")

    if result["by_strategy"]:
        print("\nBy strategy:")
        for sid, rate in sorted(result["by_strategy"].items()):
            print(f"  {sid}: {rate:.1%}")

    if result["by_persona"]:
        print("\nBy persona:")
        for pid, rate in sorted(result["by_persona"].items()):
            print(f"  {pid}: {rate:.1%}")

    if result["surprises"]:
        print(f"\nSurprises ({len(result['surprises'])}):")
        for s in result["surprises"]:
            print(
                f"  [{s['persona_id']} x {s['strategy_id']}] "
                f"predicted={s['predicted_class']}, actual={s['actual_verdict']}"
            )
    else:
        print("\nNo surprises — all non-neutral predictions matched.")


if __name__ == "__main__":
    main()
