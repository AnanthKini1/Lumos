"""
patch_turn_deltas.py

Patches stance_delta and is_pivotal on each turn to create realistic,
varied per-turn movement — including zero-shift turns, gradual builds,
and occasional pivotal spikes (|delta| >= 1.0).

Only turn.stance_delta and turn.is_pivotal are changed.
Trajectory arrays (public/private_stance_per_turn) are untouched.

Run from repo root: python backend/scripts/patch_turn_deltas.py
"""
import json
import hashlib
from pathlib import Path

SCENARIOS = Path("frontend/src/data/scenarios")
PIVOTAL_THRESHOLD = 1.0

# Delta profiles per verdict type.
# Each profile is a list of stance_delta values for turns 1-6 (or 1-7).
# "direction" will be applied by multiplying by +1 or -1 based on verdict.

PROFILES = {
    "GENUINE_BELIEF_SHIFT": [
        [0.0, -0.3,  1.2,  0.4,  0.0,  0.5,  0.1],  # initial resistance, then pivotal
        [0.0,  0.4, -0.2,  1.3,  0.0,  0.4,  0.2],  # dip before pivot turn 4
        [0.0,  0.0, -0.3,  1.5,  0.4,  0.0,  0.2],  # resistance turn 3, pivotal turn 4
        [0.0,  0.5, -0.2,  0.0,  1.4,  0.3,  0.1],  # setback then breakthrough turn 5
        [0.0,  1.1, -0.3,  0.4,  0.0,  0.4,  0.1],  # early pivot, then doubt
        [0.0,  0.4,  0.0, -0.2,  1.2,  0.3,  0.0],  # late resistance before shift
    ],
    "PARTIAL_SHIFT": [
        [0.0, -0.2,  0.0,  0.5,  0.4,  0.0,  0.1],  # early resistance, then movement
        [0.0,  0.4, -0.3,  0.0,  0.5,  0.3,  0.0],  # dip mid-conversation
        [0.0,  0.4, -0.2,  0.0,  0.5,  0.0,  0.2],  # pushback turn 3
        [0.0,  0.0, -0.2,  0.5,  0.4,  0.0,  0.2],  # slow start with dip
        [0.0,  0.5,  0.0, -0.2,  0.0,  0.5,  0.1],  # mid dip
        [0.0,  0.4, -0.3,  0.5,  0.0,  0.3,  0.0],  # bounce pattern
    ],
    "NO_MOVEMENT": [
        [0.0,  0.1, -0.1,  0.0,  0.1, -0.1,  0.0],  # oscillating
        [0.0, -0.1,  0.2, -0.1,  0.0, -0.1,  0.1],  # slight negative bias
        [0.0,  0.2, -0.2,  0.1, -0.1,  0.0,  0.0],  # cancel out
        [0.0,  0.0,  0.1, -0.1,  0.0,  0.1, -0.1],  # flat start
        [0.0, -0.2,  0.0,  0.2,  0.0, -0.1,  0.1],  # noise around zero
        [0.0,  0.1,  0.0, -0.1,  0.1,  0.0, -0.1],  # minimal movement
    ],
    "BACKFIRE": [
        [0.0, -0.3, -0.5, -0.2,  0.0, -0.3,  0.0],  # hardening mid
        [0.0, -0.2, -0.7, -0.3,  0.0, -0.2,  0.0],  # spike turn 3
        [0.0,  0.0, -0.5, -0.2, -0.5,  0.0,  0.0],  # two dips
        [0.0, -0.5, -0.2,  0.0, -0.5, -0.2,  0.1],  # steady resistance
        [0.0, -0.3,  0.0, -0.6, -0.2,  0.0, -0.2],  # delayed spike
        [0.0, -0.8, -0.2,  0.0, -0.3,  0.0,  0.1],  # early strong rejection
    ],
    "SURFACE_COMPLIANCE": [
        [0.0,  0.0,  0.1,  0.0,  0.1,  0.0,  0.0],  # barely moves
        [0.0,  0.1,  0.0,  0.0,  0.1,  0.0,  0.0],
        [0.0,  0.0,  0.0,  0.1,  0.0,  0.1,  0.0],
        [0.0,  0.1,  0.0,  0.1,  0.0,  0.0,  0.0],
        [0.0,  0.0,  0.1,  0.0,  0.0,  0.1,  0.0],
        [0.0,  0.0,  0.0,  0.0,  0.1,  0.1,  0.0],
    ],
}


def _color_category(delta: float, verdict: str) -> str | None:
    """
    Maps a per-turn delta + overall verdict to a node color category.
    Returns None for turns with no meaningful signal (gray node).

    Thresholds:
      delta <= 0.0              → None (gray)
      delta < 0                 → backfire (red)
      0 < delta < 0.4           → None (gray — too small to signal)
      delta >= 0.4 + positive verdict → genuine_persuasion (green)
      delta >= 0.4 + surface/no-move  → surface_mechanism (amber)
    """
    if delta <= 0.0:
        return None if delta == 0.0 else "backfire"
    # delta > 0
    if delta < 0.4:
        return None  # small positive — not enough signal to color
    if verdict == "SURFACE_COMPLIANCE":
        return "surface_mechanism"
    if verdict == "NO_MOVEMENT":
        return "surface_mechanism"
    if verdict in ("GENUINE_BELIEF_SHIFT", "PARTIAL_SHIFT"):
        return "genuine_persuasion"
    if verdict == "BACKFIRE":
        return "surface_mechanism"
    return "genuine_persuasion"


def get_profile(persona_id: str, strategy_id: str, verdict: str) -> list:
    profiles = PROFILES.get(verdict, PROFILES["PARTIAL_SHIFT"])
    h = int(hashlib.md5(f"{persona_id}|{strategy_id}".encode()).hexdigest(), 16)
    return profiles[h % len(profiles)]


if __name__ == "__main__":
    for path in sorted(SCENARIOS.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        persona_id = path.stem.split("__")[0]

        for outcome in data["outcomes"]:
            sid = outcome["strategy_id"]
            verdict = outcome.get("verdict", "PARTIAL_SHIFT")
            turns = outcome["turns"]
            n = len(turns)

            profile = get_profile(persona_id, sid, verdict)

            for i, turn in enumerate(turns):
                delta = round(profile[i] if i < len(profile) else 0.0, 1)
                turn["stance_delta"] = delta
                turn["is_pivotal"] = abs(delta) >= PIVOTAL_THRESHOLD
                turn["color_category"] = _color_category(delta, verdict)

        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Done.")
