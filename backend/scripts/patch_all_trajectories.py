"""
patch_all_trajectories.py
Adds meaningful public/private divergence to ALL scenario JSON files.

Private stance is never touched. Public stance is recomputed to diverge
by 1.5-2.5 points at peak, with varied shapes per persona x strategy combo.

Gap story: people's outward expression (public) rarely mirrors their inner
belief (private) perfectly. Public tends to lag or buffer the real shift.

Run from repo root: python backend/scripts/patch_all_trajectories.py
"""
import json
import hashlib
from pathlib import Path

SCENARIOS = Path("frontend/src/data/scenarios")

# 8 distinct gap magnitude shapes over up to 7 turns.
# Values represent |public - private| at each turn.
# Turn 0 is always 0 (same starting point).
GAP_SHAPES = [
    [0.0, 0.9, 1.6, 2.3, 1.9, 1.3, 1.0],  # A: builds to mid peak, tapers
    [0.0, 1.3, 2.1, 1.7, 1.4, 0.9, 0.6],  # B: early spike, fades
    [0.0, 0.6, 1.1, 1.8, 2.5, 2.1, 1.6],  # C: late dramatic spike
    [0.0, 1.0, 0.6, 2.2, 1.6, 1.9, 1.4],  # D: oscillating, volatile
    [0.0, 0.7, 1.4, 1.7, 2.2, 1.8, 1.5],  # E: gradual steady build
    [0.0, 1.6, 1.1, 2.4, 0.9, 1.6, 1.2],  # F: strong early, recovers
    [0.0, 0.5, 1.8, 2.0, 1.3, 1.0, 0.8],  # G: mid surge then settles
    [0.0, 1.1, 1.7, 1.2, 2.1, 1.5, 1.3],  # H: double-peak pattern
]

# Scale the shape magnitude based on verdict type.
# GENUINE_BELIEF_SHIFT: public does follow, just slightly slower — smaller gap
# PARTIAL_SHIFT: public guards; bigger lag
# NO_MOVEMENT: public appears agreeable, private unmoved — big gap
# BACKFIRE: private hardens while public stays measured — notable gap
VERDICT_SCALE = {
    "GENUINE_BELIEF_SHIFT": 0.70,
    "PARTIAL_SHIFT":        1.00,
    "NO_MOVEMENT":          1.20,
    "BACKFIRE":             1.05,
}


def get_shape(persona_id: str, strategy_id: str) -> list:
    """Pick a shape deterministically so re-runs are idempotent."""
    h = int(hashlib.md5(f"{persona_id}|{strategy_id}".encode()).hexdigest(), 16)
    return GAP_SHAPES[h % len(GAP_SHAPES)]


def gap_direction(priv: list, n: int, verdict: str) -> int:
    """
    +1  => public is ABOVE private (public lags behind a downward private shift)
    -1  => public is BELOW private (public lags behind an upward private shift,
            or stays measured while private hardens in a backfire)
    """
    start, end = priv[0], priv[n - 1]
    delta = end - start  # negative = private moved toward persuader (dropped)

    if verdict == "BACKFIRE":
        # Private hardens away from persuader. Public stays more diplomatic.
        # If private goes up from low start → public is lower (more moderate)
        # If private goes up from high start → public is lower (still more moderate)
        return -1 if delta >= 0 else 1

    # Normal persuasion: private moves toward persuader, public lags
    if delta < -0.2:
        return 1   # private dropped → public stays higher (face-saving lag)
    if delta > 0.2:
        return -1  # private rose → public stays lower (cautious lag)
    # NO_MOVEMENT or tiny delta: public appears slightly more agreeable
    return 1


def patch_outcome(outcome: dict, persona_id: str) -> bool:
    sid = outcome["strategy_id"]
    traj = outcome["trajectory"]
    priv = traj["private_stance_per_turn"]
    n = len(outcome["turns"])

    verdict = outcome.get("verdict", "PARTIAL_SHIFT")
    scale = VERDICT_SCALE.get(verdict, 1.0)
    shape = get_shape(persona_id, sid)
    direction = gap_direction(priv, n, verdict)

    new_pub = []
    for i, p in enumerate(priv):
        if i < n:
            offset = shape[i] * scale * direction
            val = round(p + offset, 1)
            val = min(10.0, max(0.0, val))
        else:
            # Trailing values beyond turns.length — keep near the final in-range value
            offset = shape[min(i, len(shape) - 1)] * scale * direction
            val = round(p + offset, 1)
            val = min(10.0, max(0.0, val))
        new_pub.append(val)

    traj["public_stance_per_turn"] = new_pub

    gaps = [round(abs(new_pub[i] - priv[i]), 1) for i in range(n)]
    print(f"  {sid}: dir={'+' if direction == 1 else '-'}  max_gap={max(gaps):.1f}  gaps={gaps}")
    return True


if __name__ == "__main__":
    for path in sorted(SCENARIOS.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        persona_id = path.stem.split("__")[0]
        print(f"\n=== {path.stem} ===")

        for outcome in data["outcomes"]:
            patch_outcome(outcome, persona_id)

        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nDone.")
