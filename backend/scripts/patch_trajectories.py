"""
Patch public_stance_per_turn arrays to create meaningful divergence
from private_stance_per_turn. Private stance is left unchanged.

The gap tells the story: someone can publicly appear more open (or more
resistant) than they actually are privately. For backfire cases the gap
is already visible; we focus on persuasion cases where it's currently flat.

Run from repo root: python backend/scripts/patch_trajectories.py
"""
import json
from pathlib import Path

SCENARIOS = Path("frontend/src/data/scenarios")

# Only public_stance_per_turn is changed. Private stays as-is.
# Arrays keep original length so trailing values don't break anything;
# the chart slices to turns.length (6) anyway.
PATCHES = {
    "persona_skeptical_traditionalist__topic_return_to_office": {
        # Karen starts at 7.0 (pro-RTO). Persuader tries to lower her stance.
        # Gap story: publicly she sounds composed/polite while privately
        # she's either more moved or more resistant than she lets on.
        "strategy_common_ground": {
            # NO_MOVEMENT. Public stays higher (more resistant) than private dips.
            # Private: [7.0, 7.0, 6.5, 7.2, 6.5, 6.5, 6.5, 6.2]
            "public_stance_per_turn": [7.0, 6.5, 5.8, 6.0, 5.5, 5.8, 6.0, 6.2],
        },
        "strategy_emotional_appeal": {
            # NO_MOVEMENT. Private dipped to 5.5 emotionally; public stayed guarded.
            # Private: [7.0, 6.5, 5.5, 5.5, 5.5, 6.5, 6.2, 6.1]
            "public_stance_per_turn": [7.0, 7.0, 7.0, 7.2, 7.5, 7.5, 7.0, 6.5],
        },
        "strategy_statistical_logical": {
            # PARTIAL_SHIFT. Private swung hard (to 3.5); public lagged significantly.
            # Private: [7.0, 6.5, 6.0, 4.5, 4.5, 6.5, 3.5, 5.0]
            "public_stance_per_turn": [7.0, 6.8, 6.8, 6.5, 6.2, 7.2, 5.5, 5.5],
        },
        "strategy_authority_expert": {
            # PARTIAL_SHIFT. Private quietly lowered; public maintained composure.
            # Private: [7.0, 7.2, 6.0, 6.5, 5.5, 5.5, 5.5, 5.5]
            "public_stance_per_turn": [7.0, 7.5, 7.2, 7.5, 7.0, 6.8, 6.5, 6.0],
        },
        "strategy_personal_narrative": {
            # PARTIAL_SHIFT. Stories moved private more than Karen let on publicly.
            # Private: [7.0, 6.0, 6.5, 5.5, 5.5, 5.5, 5.2, 5.0]
            "public_stance_per_turn": [7.0, 6.8, 7.2, 7.0, 6.8, 6.5, 6.0, 5.8],
        },
        "strategy_social_proof": {
            # PARTIAL_SHIFT. Public agrees with the data more than private belief moved.
            # Private: [7.0, 6.5, 5.5, 6.5, 5.5, 5.5, 5.5, 5.0]
            "public_stance_per_turn": [7.0, 7.0, 6.8, 7.5, 7.2, 7.0, 6.8, 6.0],
        },
    },
    "persona_faith_community_anchor__topic_return_to_office": {
        # Pastor Raymond starts at 7.5.
        # Authority Expert and Social Proof already have strong gaps — leave unchanged.
        "strategy_common_ground": {
            # GENUINE_BELIEF_SHIFT. Private leads; public expression catches up slowly.
            # Private: [7.5, 7.8, 8.2, 8.7, 9.2, 9.7, 9.9]
            "public_stance_per_turn": [7.5, 7.5, 7.8, 8.0, 8.3, 8.8, 9.2],
        },
        "strategy_emotional_appeal": {
            # PARTIAL_SHIFT. Private moved more than public expression showed.
            # Private: [7.5, 7.6, 7.9, 8.2, 8.5, 8.7, 8.9]
            "public_stance_per_turn": [7.5, 7.4, 7.5, 7.7, 7.9, 8.0, 8.2],
        },
        "strategy_statistical_logical": {
            # NO_MOVEMENT. He publicly goes along with the data; privately unmoved.
            # Private: [7.5, 7.6, 7.4, 7.7, 7.6, 7.4, 7.6]
            "public_stance_per_turn": [7.5, 7.8, 8.2, 8.5, 8.3, 8.5, 8.2],
        },
        "strategy_personal_narrative": {
            # PARTIAL_SHIFT. Private moved more than his measured public response showed.
            # Private: [7.5, 7.6, 7.9, 8.2, 8.5, 8.7, 8.9]
            "public_stance_per_turn": [7.5, 7.4, 7.5, 7.6, 7.8, 7.9, 8.1],
        },
        # strategy_authority_expert and strategy_social_proof left unchanged — already strong gaps
    },
}


def patch(scenario_id: str, strategy_patches: dict) -> None:
    path = SCENARIOS / f"{scenario_id}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    for outcome in data["outcomes"]:
        sid = outcome["strategy_id"]
        if sid not in strategy_patches:
            continue
        changes = strategy_patches[sid]
        if "public_stance_per_turn" in changes:
            old_pub = outcome["trajectory"]["public_stance_per_turn"]
            new_pub = changes["public_stance_per_turn"]
            outcome["trajectory"]["public_stance_per_turn"] = new_pub
            priv = outcome["trajectory"]["private_stance_per_turn"]
            gaps = [round(abs(p - r), 1) for p, r in zip(new_pub, priv)]
            print(f"  {sid}: max gap = {max(gaps):.1f}  gaps={gaps}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {scenario_id}\n")


if __name__ == "__main__":
    for scenario_id, strategy_patches in PATCHES.items():
        print(f"=== {scenario_id} ===")
        patch(scenario_id, strategy_patches)
    print("Done.")
