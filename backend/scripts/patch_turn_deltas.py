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
        [0.0,  0.3,  1.2,  0.4,  0.3,  0.0,  0.1],  # pivotal turn 3
        [0.0,  0.2,  0.4,  1.3,  0.2,  0.0,  0.2],  # pivotal turn 4
        [0.0,  0.5,  0.0,  1.5,  0.3,  0.0,  0.2],  # pivotal turn 4, zero at 3
        [0.0,  0.3,  0.2,  0.0,  1.4,  0.3,  0.1],  # pivotal turn 5
        [0.0,  1.1,  0.4,  0.0,  0.3,  0.2,  0.1],  # early pivot turn 2
        [0.0,  0.2,  0.0,  0.4,  1.2,  0.3,  0.0],  # late build
    ],
    "PARTIAL_SHIFT": [
        [0.0,  0.3,  0.0,  0.5,  0.4,  0.2,  0.1],  # zero at turn 3
        [0.0,  0.2,  0.5,  0.0,  0.4,  0.3,  0.0],  # zeros at 4 and 7
        [0.0,  0.4,  0.3,  0.0,  0.3,  0.2,  0.1],  # zero at 4
        [0.0,  0.0,  0.4,  0.5,  0.2,  0.0,  0.2],  # zeros at 2 and 6
        [0.0,  0.5,  0.0,  0.3,  0.0,  0.5,  0.1],  # alternating zeros
        [0.0,  0.2,  0.3,  0.4,  0.0,  0.3,  0.0],  # trailing zero
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

        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Done.")
