"""
sync_gaps_and_verdicts.py

After patching public_stance_per_turn, this script:
1. Recomputes trajectory.gap_per_turn from actual public/private arrays
2. Updates cognitive_scores.public_private_gap_score to the new average
3. Downgrades GENUINE_BELIEF_SHIFT → PARTIAL_SHIFT for any outcome whose
   private delta is below the new threshold (2.5), keeping all other
   stored verdicts (PARTIAL, NO_MOVEMENT, SURFACE_COMPLIANCE, BACKFIRE) as-is.

Run from repo root: python backend/scripts/sync_gaps_and_verdicts.py
"""
import json
from pathlib import Path

SCENARIOS = Path("frontend/src/data/scenarios")

NEW_GENUINE_MIN_DELTA = 2.5   # raised from 2.0

PARTIAL_REASONING_TEMPLATE = (
    "Private stance shifted {delta:+.1f} points — meaningful movement but below the "
    "genuine shift threshold ({threshold}). Persistence: {persistence}."
)


def sync(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False

    for outcome in data["outcomes"]:
        traj = outcome["trajectory"]
        priv = traj["private_stance_per_turn"]
        pub  = traj["public_stance_per_turn"]
        n    = len(outcome["turns"])

        # 1. Recompute gap_per_turn
        new_gaps = [round(abs(pub[i] - priv[i]), 2) for i in range(len(priv))]
        traj["gap_per_turn"] = new_gaps

        # 2. Recompute public_private_gap_score (avg over actual turns only)
        avg_gap = sum(new_gaps[:n]) / n
        old_gap = outcome["cognitive_scores"]["public_private_gap_score"]
        outcome["cognitive_scores"]["public_private_gap_score"] = round(avg_gap, 2)

        # 3. Downgrade GENUINE_BELIEF_SHIFT if below new threshold
        if outcome.get("verdict") == "GENUINE_BELIEF_SHIFT":
            private_delta = priv[n - 1] - priv[0]
            if abs(private_delta) < NEW_GENUINE_MIN_DELTA:
                persistence = outcome["cognitive_scores"].get("persistence", "unknown")
                outcome["verdict"] = "PARTIAL_SHIFT"
                outcome["verdict_reasoning"] = PARTIAL_REASONING_TEMPLATE.format(
                    delta=private_delta,
                    threshold=NEW_GENUINE_MIN_DELTA,
                    persistence=persistence,
                )
                print(
                    f"  GENUINE->PARTIAL  delta={private_delta:+.1f}  "
                    f"gap {old_gap:.2f}->{avg_gap:.2f}  {outcome['strategy_id']}"
                )
                changed = True
            else:
                print(
                    f"  GENUINE kept     delta={private_delta:+.1f}  "
                    f"gap {old_gap:.2f}->{avg_gap:.2f}  {outcome['strategy_id']}"
                )
        else:
            # Just log gap updates for non-GENUINE
            if abs(old_gap - avg_gap) > 0.05:
                changed = True  # still need to save

    if changed or True:  # always save to update gap arrays
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    for path in sorted(SCENARIOS.glob("*.json")):
        print(f"\n=== {path.stem} ===")
        sync(path)
    print("\nDone.")
