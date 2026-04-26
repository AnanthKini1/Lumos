"""
Regenerate synthesis_paragraph for every strategy outcome in one or more
frontend scenario JSON files, using the updated strategy judge prompts that
mandate exact mechanism display names with author-year citations.

Also regenerates overall_synthesis with the updated pipeline prompt.

Usage (run from backend/):
  python scripts/regen_synthesis.py --scenario persona_skeptical_traditionalist__topic_return_to_office
  python scripts/regen_synthesis.py --all

Options:
  --scenario ID   Regenerate a single scenario file (omit .json extension)
  --all           Regenerate all scenario files in frontend/src/data/scenarios/
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Allow imports from backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.strategy_judge import run_strategy_judge
from data.loader import load_cognitive_mechanisms, load_strategy
from models import (
    CoolingOff,
    ConversationTurn,
    MechanismClassification,
    PersonaTurnOutput,
    EmotionalReaction,
    IdentityThreat,
    ResponseInclination,
    PrimaryEmotion,
    StrategyOutcome,
    SimulationOutput,
)
import anthropic
from config import ANTHROPIC_API_KEY, API_MAX_RETRIES, MODEL_ID

SCENARIOS_DIR = Path(__file__).parent.parent.parent / "frontend" / "src" / "data" / "scenarios"

_SYNTHESIS_MAX_TOKENS = 300


async def regen_overall_synthesis(persona_name: str, topic_name: str, outcomes: list[dict]) -> str:
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY, max_retries=API_MAX_RETRIES)
    lines = [
        f"  - {o['strategy_id']}: {o['verdict']} "
        f"(private shift: {o['trajectory']['private_stance_per_turn'][-1] - o['trajectory']['private_stance_per_turn'][0]:+.1f})"
        for o in outcomes
    ]
    summary = "\n".join(lines)
    user = (
        f"Persona: {persona_name}\nTopic: {topic_name}\n\nStrategy results:\n{summary}\n\n"
        "Write exactly 2 complete sentences in plain English prose summarizing what these "
        "results reveal about persuasion for this persona type. Name which strategies worked "
        "and why, and which failed and why. Be specific. "
        "When referencing cognitive mechanisms, use their exact display names followed by "
        "the author-year citation in parentheses "
        "(e.g. 'Identity-Protective Cognition (Kahan, 2010)', 'Reactance (Brehm, 1966)', "
        "'Narrative Transportation (Green & Brock, 2000)'). "
        "Do not use slashes, bullet points, or list formatting. Return only the 2 sentences."
    )
    msg = await client.messages.create(
        model=MODEL_ID,
        max_tokens=_SYNTHESIS_MAX_TOKENS,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


def _turns_from_raw(raw_turns: list[dict]) -> list[ConversationTurn]:
    """Re-hydrate ConversationTurn objects from stored JSON dicts."""
    turns = []
    for t in raw_turns:
        po_raw = t["persona_output"]
        er_raw = po_raw["emotional_reaction"]
        it_raw = po_raw["identity_threat"]
        po = PersonaTurnOutput(
            internal_monologue=po_raw["internal_monologue"],
            emotional_reaction=EmotionalReaction(
                primary_emotion=PrimaryEmotion(er_raw["primary_emotion"]),
                intensity=er_raw["intensity"],
                trigger=er_raw.get("trigger", ""),
            ),
            identity_threat=IdentityThreat(
                threatened=it_raw["threatened"],
                what_was_threatened=it_raw.get("what_was_threatened"),
                response_inclination=ResponseInclination(it_raw.get("response_inclination", "accept")),
            ),
            private_stance=po_raw["private_stance"],
            public_stance=po_raw["public_stance"],
            private_stance_change_reason=po_raw.get("private_stance_change_reason", ""),
            memory_to_carry_forward=po_raw.get("memory_to_carry_forward", ""),
            public_response=po_raw.get("public_response", ""),
        )
        mc_raw = t.get("mechanism_classification")
        mc = None
        if mc_raw:
            mc = MechanismClassification(
                primary_mechanism_id=mc_raw["primary_mechanism_id"],
                secondary_mechanism_id=mc_raw.get("secondary_mechanism_id"),
                explanation=mc_raw.get("explanation", ""),
                evidence_quotes=mc_raw.get("evidence_quotes", []),
                color_category=mc_raw.get("color_category", "surface_mechanism"),
                intensity=mc_raw.get("intensity", 0.0),
            )
        turns.append(ConversationTurn(
            turn_number=t["turn_number"],
            persuader_message=t["persuader_message"],
            persuader_strategy_note=t.get("persuader_strategy_note", ""),
            persona_output=po,
            stance_delta=t.get("stance_delta", 0.0),
            is_pivotal=t.get("is_pivotal", False),
            is_inflection_point=t.get("is_inflection_point", False),
            mechanism_classification=mc,
            per_turn_cognitive_scores=t.get("per_turn_cognitive_scores"),
            color_category=t.get("color_category"),
            intensity=t.get("intensity"),
        ))
    return turns


async def regen_scenario(path: Path) -> None:
    print(f"Processing: {path.name}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    mechanisms = load_cognitive_mechanisms()
    persona_name = data["metadata"]["persona"]["display_name"]
    topic_name   = data["metadata"]["topic"]["display_name"]

    async def regen_outcome(outcome_raw: dict) -> dict:
        strategy_id = outcome_raw["strategy_id"]
        print(f"  Regenerating synthesis for {strategy_id}...")
        try:
            strategy = load_strategy(strategy_id)
        except Exception as e:
            print(f"  WARN: could not load strategy {strategy_id}: {e}")
            return outcome_raw

        cooling_raw = outcome_raw.get("cooling_off", {})
        cooling = CoolingOff(
            post_conversation_reflection=cooling_raw.get("post_conversation_reflection", ""),
            post_reflection_stance=cooling_raw.get("post_reflection_stance",
                outcome_raw["trajectory"]["private_stance_per_turn"][-1]),
        )
        turns = _turns_from_raw(outcome_raw["turns"])

        try:
            synthesis = await run_strategy_judge(strategy, turns, cooling, mechanisms)
            outcome_raw["synthesis_paragraph"] = synthesis
            print(f"  OK: {strategy_id}")
        except Exception as e:
            print(f"  WARN: judge failed for {strategy_id}: {e}")

        return outcome_raw

    tasks = [regen_outcome(o) for o in data["outcomes"]]
    data["outcomes"] = await asyncio.gather(*tasks)

    print(f"  Regenerating overall synthesis...")
    try:
        data["overall_synthesis"] = await regen_overall_synthesis(
            persona_name, topic_name, data["outcomes"]
        )
        print(f"  OK: overall_synthesis")
    except Exception as e:
        print(f"  WARN: overall synthesis failed: {e}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {path.name}\n")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate synthesis paragraphs in scenario files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", help="Scenario file name without .json extension")
    group.add_argument("--all", action="store_true", help="Regenerate all scenario files")
    args = parser.parse_args()

    if args.all:
        paths = sorted(SCENARIOS_DIR.glob("*.json"))
    else:
        paths = [SCENARIOS_DIR / f"{args.scenario}.json"]

    for path in paths:
        if not path.exists():
            print(f"ERROR: {path} not found")
            continue
        await regen_scenario(path)

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
