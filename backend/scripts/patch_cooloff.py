"""
Patch post_reflection_stance values so the cool-off period shows
realistic post-conversation movement rather than being identical
to the final private stance.

Logic:
  GENUINE_BELIEF_SHIFT  → slight consolidation, small reversion (~0.3-0.5 toward original)
  PARTIAL_SHIFT         → moderate reversion (~0.5-0.8 toward original)
  NO_MOVEMENT           → significant reversion (~0.6-1.0 toward original)
  BACKFIRE              → slight further hardening (~0.2 away from original)

Run from repo root: python backend/scripts/patch_cooloff.py
"""
import json
from pathlib import Path

SCENARIOS = Path("frontend/src/data/scenarios")

# { scenario_id: { strategy_id: new_post_reflection_stance } }
PATCHES = {
    "persona_skeptical_traditionalist__topic_return_to_office": {
        # Karen starts around 7.0. Higher = more pro-RTO.
        # NO_MOVEMENT strategies: significant reversion back toward 7.0
        "strategy_common_ground":       6.7,   # was 6.2, reverts toward start
        "strategy_emotional_appeal":    6.8,   # was 6.1, reverts toward start
        # PARTIAL_SHIFT strategies: moderate reversion
        "strategy_statistical_logical": 5.5,   # was 5.0, slight reversion
        "strategy_authority_expert":    5.9,   # was 5.5, slight reversion
        "strategy_personal_narrative":  5.4,   # was 5.0, slight reversion
        "strategy_social_proof":        5.6,   # was 5.0, slight reversion
    },
    "persona_faith_community_anchor__topic_return_to_office": {
        # Pastor Raymond starts around 7.3.
        # GENUINE_BELIEF_SHIFT: slight consolidation reversion
        "strategy_common_ground":       9.5,   # was 9.9, slight settle
        # PARTIAL_SHIFT: moderate reversion
        "strategy_emotional_appeal":    8.1,   # was 8.5, moderate reversion
        "strategy_personal_narrative":  8.2,   # was 8.5, moderate reversion
        # NO_MOVEMENT: reversion toward original
        "strategy_statistical_logical": 7.8,   # was 7.6, back toward start
        # BACKFIRE: slight further hardening away from persuader
        "strategy_authority_expert":    6.2,   # was 6.5, hardens slightly
        "strategy_social_proof":        6.1,   # was 6.5, hardens slightly
    },
}


def patch(scenario_id: str, stance_map: dict) -> None:
    path = SCENARIOS / f"{scenario_id}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    for outcome in data["outcomes"]:
        sid = outcome["strategy_id"]
        if sid in stance_map:
            old = outcome["cooling_off"]["post_reflection_stance"]
            new = stance_map[sid]
            outcome["cooling_off"]["post_reflection_stance"] = new
            # Also update trajectory persistence field if present
            if "persistence" in outcome.get("cognitive_scores", {}):
                pass  # leave persistence verdict unchanged
            print(f"  {sid}: {old} -> {new}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {scenario_id}\n")


if __name__ == "__main__":
    for scenario_id, stance_map in PATCHES.items():
        print(f"=== {scenario_id} ===")
        patch(scenario_id, stance_map)
    print("Done.")
