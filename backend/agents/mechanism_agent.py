"""
WS-B — Mechanism classification agent.

For each pivotal moment in a conversation (where private stance shifted >= 1.0 point),
classifies which cognitive mechanism from the library best explains the shift.

This makes every interpretation traceable to a published research framework.

The judge receives:
- The persuader's exact phrase that triggered the shift
- The persona's internal monologue at that moment
- The magnitude of the stance shift
- The full mechanism library as structured context

Returns a MechanismClassification with primary mechanism, optional secondary,
a 2-3 sentence explanation citing monologue evidence, and the color category
used for frontend highlighting.

Does NOT know about:
- Conversation sequencing (conversation_loop.py)
- Scoring (measurement/scorer.py)
- Pipeline assembly (pipeline.py)
"""

import asyncio

import anthropic

from config import ANTHROPIC_API_KEY, API_MAX_RETRIES, MAX_TOKENS_JUDGE, MODEL_ID
from models import MechanismClassification

_MECHANISM_TOOL_NAME = "classify_cognitive_mechanism"

_MECHANISM_TOOL = {
    "name": _MECHANISM_TOOL_NAME,
    "description": (
        "Classify which cognitive mechanism best explains this pivotal moment. "
        "Choose from the mechanism library provided in your context."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "primary_mechanism_id": {
                "type": "string",
                "description": "The id of the mechanism that best explains this moment. Must match an id in the library.",
            },
            "secondary_mechanism_id": {
                "type": "string",
                "description": "Optional second mechanism id if two are active. Leave empty string if only one applies.",
            },
            "explanation": {
                "type": "string",
                "description": (
                    "2-3 sentences explaining why this mechanism applies. "
                    "Cite specific phrases from the persona's monologue as evidence."
                ),
            },
            "evidence_quote_1": {
                "type": "string",
                "description": "A specific phrase from the persona's monologue that is diagnostic evidence for this mechanism.",
            },
            "evidence_quote_2": {
                "type": "string",
                "description": "A second specific phrase from the monologue. Leave empty if only one strong quote exists.",
            },
        },
        "required": [
            "primary_mechanism_id",
            "secondary_mechanism_id",
            "explanation",
            "evidence_quote_1",
            "evidence_quote_2",
        ],
    },
}

# Shared semaphore to avoid bursting judge calls at Haiku tier limits
_MECHANISM_SEMAPHORE = asyncio.Semaphore(4)


def _build_mechanism_context(mechanisms: list[dict]) -> str:
    lines = ["COGNITIVE MECHANISM LIBRARY:"]
    for m in mechanisms:
        lines.append(f"\nID: {m['id']}")
        lines.append(f"  Name: {m['display_name']} ({m['framework']})")
        lines.append(f"  Definition: {m['operational_definition']}")
        lines.append(f"  Category: {m['category']}")
        lines.append(f"  Diagnostic indicators:")
        for indicator in m["diagnostic_indicators"]:
            lines.append(f"    - {indicator}")
    return "\n".join(lines)


async def classify_mechanism(
    persuader_phrase: str,
    persona_monologue: str,
    stance_delta: float,
    mechanisms: list[dict],
) -> MechanismClassification:
    """
    Classify the cognitive mechanism active at one pivotal moment.

    persuader_phrase: the exact message that triggered the stance shift
    persona_monologue: the persona's internal monologue for this turn
    stance_delta: how much private stance moved this turn (signed float)
    mechanisms: the loaded cognitive mechanism library
    """
    async with _MECHANISM_SEMAPHORE:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY, max_retries=API_MAX_RETRIES)

        mechanism_context = _build_mechanism_context(mechanisms)

        # Build a lookup: mechanism id → category (for color derivation)
        category_map = {m["id"]: m["category"] for m in mechanisms}
        valid_ids = set(category_map.keys())

        system = (
            f"{mechanism_context}\n\n"
            "You are a cognitive science analyst. Given a pivotal moment in a persuasion "
            "conversation — where the persona's private belief stance shifted noticeably — "
            "identify which cognitive mechanism from the library above best explains the shift.\n\n"
            "Your classification must be based entirely on evidence in the persona's internal "
            "monologue. Do not infer mechanisms that aren't visible in the text. If multiple "
            "mechanisms are active, name the dominant one first."
        )

        direction = "toward" if stance_delta < 0 else "away from"
        user = (
            f"PERSUADER SAID:\n\"{persuader_phrase}\"\n\n"
            f"PERSONA'S INTERNAL MONOLOGUE:\n\"{persona_monologue}\"\n\n"
            f"STANCE SHIFT: {abs(stance_delta):.1f} points {direction} persuader's position "
            f"(delta: {stance_delta:+.1f})\n\n"
            f"Classify the primary cognitive mechanism active in this moment. "
            f"Use the {_MECHANISM_TOOL_NAME} tool."
        )

        response = await client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS_JUDGE,
            system=system,
            tools=[_MECHANISM_TOOL],
            tool_choice={"type": "tool", "name": _MECHANISM_TOOL_NAME},
            messages=[{"role": "user", "content": user}],
        )

        tool_block = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_block is None:
            raise ValueError(f"Mechanism agent did not invoke tool. Response: {response.content}")
        raw = tool_block.input

        # Validate and fallback for primary mechanism id
        primary_id = raw.get("primary_mechanism_id", "")
        if primary_id not in valid_ids:
            # Best-effort: pick the first mechanism whose category matches the direction
            # (stance moved away = backfire, stance moved toward = persuasion)
            fallback_cat = "backfire" if stance_delta > 0 else "genuine_persuasion"
            primary_id = next(
                (m["id"] for m in mechanisms if m["category"] == fallback_cat),
                mechanisms[0]["id"],
            )

        secondary_raw = raw.get("secondary_mechanism_id", "") or None
        secondary_id = secondary_raw if secondary_raw and secondary_raw in valid_ids else None

        evidence_quotes = [
            q for q in [raw.get("evidence_quote_1", ""), raw.get("evidence_quote_2", "")]
            if q.strip()
        ]

        color_category = category_map.get(primary_id, "surface_mechanism")
        max_abs = 10.0  # stance scale is 0-10; normalize intensity
        intensity = round(min(abs(stance_delta) / max_abs, 1.0), 3)

        return MechanismClassification(
            primary_mechanism_id=primary_id,
            secondary_mechanism_id=secondary_id,
            explanation=raw.get("explanation", ""),
            evidence_quotes=evidence_quotes,
            color_category=color_category,
            intensity=intensity,
        )
