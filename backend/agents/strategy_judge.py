"""
WS-B — Strategy-specific mechanism judges.

Each of the 6 persuasion strategies has a dedicated judge that specializes in
evaluating whether the cognitive mechanism that strategy is academically designed
to activate actually fired — and if not, what blocked it.

Unlike the generic mechanism_agent (which labels any pivotal turn), the strategy
judge takes the full conversation and asks a strategy-specific question:
"Did what was supposed to happen, happen?" — grounded in the academic framework
cited in each strategy's JSON definition.

One call per strategy conversation, after cooling-off completes. Output replaces
the generic synthesis_paragraph with a mechanism-grounded analysis.
"""

import asyncio
import json

import anthropic

from config import ANTHROPIC_API_KEY, API_MAX_RETRIES, MAX_TOKENS_JUDGE, MODEL_ID
from models import ConversationTurn, CoolingOff, StrategyDefinition

_JUDGE_SEMAPHORE = asyncio.Semaphore(4)

# Maps each strategy to the mechanisms it is designed to activate (targets)
# and the mechanisms most likely to block or reverse it (risks).
# Derived from the academic frameworks cited in the strategy JSON files.
_STRATEGY_MECHANISM_MAP: dict[str, dict[str, list[str]]] = {
    "strategy_personal_narrative": {
        "targets": ["mechanism_narrative_transportation", "mechanism_affect_heuristic"],
        "risks": ["mechanism_cognitive_dissonance_reduction", "mechanism_reactance"],
    },
    "strategy_authority_expert": {
        "targets": ["mechanism_central_route_elaboration"],
        "risks": [
            "mechanism_source_credibility_discounting",
            "mechanism_identity_protective_cognition",
            "mechanism_reactance",
        ],
    },
    "strategy_common_ground": {
        "targets": ["mechanism_cognitive_dissonance_reduction"],
        "risks": ["mechanism_identity_protective_cognition", "mechanism_motivated_reasoning"],
    },
    "strategy_emotional_appeal": {
        "targets": ["mechanism_affect_heuristic", "mechanism_narrative_transportation"],
        "risks": ["mechanism_reactance", "mechanism_motivated_reasoning"],
    },
    "strategy_statistical_logical": {
        "targets": ["mechanism_central_route_elaboration", "mechanism_anchoring"],
        "risks": ["mechanism_motivated_reasoning", "mechanism_source_credibility_discounting"],
    },
    "strategy_social_proof": {
        "targets": ["mechanism_peripheral_route_compliance"],
        "risks": ["mechanism_reactance", "mechanism_identity_protective_cognition"],
    },
}


def _build_system_prompt(strategy: StrategyDefinition, mechanisms: list[dict]) -> str:
    mechanism_map = {m["id"]: m for m in mechanisms}
    mapping = _STRATEGY_MECHANISM_MAP.get(strategy.id, {"targets": [], "risks": []})
    target_ids = mapping["targets"]
    risk_ids = mapping["risks"]

    lines = [
        f"STRATEGY: {strategy.display_name}",
        f"Academic framework: {strategy.academic_citation.framework}",
        f"What this strategy does: {strategy.one_line_description}",
        "",
        "YOUR ROLE:",
        "You are the dedicated evaluator for this specific persuasion strategy.",
        "You specialize in one question: did the cognitive mechanism this strategy was",
        "designed to activate actually fire in this conversation — and why or why not?",
        "Every claim you make must be anchored to specific evidence from the transcript.",
        "",
        "TARGET MECHANISMS — what this strategy is designed to activate:",
    ]

    for mid in target_ids:
        m = mechanism_map.get(mid)
        if not m:
            continue
        lines += [
            f"",
            f"  [{m['id']}] {m['display_name']} ({m['framework']})",
            f"  Definition: {m['operational_definition']}",
            f"  Signs the mechanism fired (look for these in the monologue):",
        ]
        for sig in m.get("behavioral_signals", []):
            lines.append(f"    + {sig}")
        for ind in m.get("diagnostic_indicators", []):
            lines.append(f"    + {ind}")
        anchor = m.get("scoring_anchor", {})
        if anchor:
            lines.append(
                f"  Scoring anchor: "
                f"LOW = {anchor.get('low', '')} | HIGH = {anchor.get('high', '')}"
            )

    lines += ["", "BACKFIRE MECHANISMS — what can block or reverse this strategy:"]

    for mid in risk_ids:
        m = mechanism_map.get(mid)
        if not m:
            continue
        lines += [
            f"",
            f"  [{m['id']}] {m['display_name']} ({m['framework']})",
            f"  Definition: {m['operational_definition']}",
            f"  Warning signs (if you see these, the strategy was blocked):",
        ]
        for sig in m.get("behavioral_signals", []):
            lines.append(f"    - {sig}")

    lines += [
        "",
        "WHAT TO WRITE:",
        "Write exactly 2-3 sentences analyzing this conversation through the lens above.",
        "Sentence 1: State whether the target mechanism activated, partially activated,",
        "  or was blocked — cite one specific quote from the monologue as evidence.",
        "Sentence 2: Name the dominant mechanism (target or backfire) and explain WHY",
        "  it applies, referencing the mechanism's diagnostic criteria.",
        "Sentence 3 (if needed): If a backfire mechanism interfered, name it and cite",
        "  a specific signal from the transcript that confirms it.",
        "CRITICAL: When naming any mechanism, use its EXACT display name as listed above",
        "  (e.g. 'Identity-Protective Cognition', 'Narrative Transportation', 'Reactance').",
        "  Include the author-year citation in parentheses after the name",
        "  (e.g. 'Identity-Protective Cognition (Kahan, 2010)').",
        "  Do not paraphrase, abbreviate, or invent alternate names for mechanisms.",
        "Return only the paragraph — no headers, no extra text.",
    ]

    return "\n".join(lines)


def _serialize_transcript(turns: list[ConversationTurn], cooling_off: CoolingOff) -> str:
    turn_data = []
    for t in turns:
        po = t.persona_output
        turn_data.append({
            "turn": t.turn_number,
            "persuader": t.persuader_message,
            "monologue": po.internal_monologue,
            "emotion": (
                f"{po.emotional_reaction.primary_emotion.value} "
                f"(intensity {po.emotional_reaction.intensity})"
            ),
            "identity_threat": po.identity_threat.threatened,
            "private_stance": po.private_stance,
            "private_stance_change_reason": po.private_stance_change_reason,
            "memory_to_carry_forward": po.memory_to_carry_forward,
            "public_response": po.public_response,
        })
    return (
        json.dumps(turn_data, indent=2)
        + f"\n\nCOOLING-OFF STANCE: {cooling_off.post_reflection_stance:.1f}"
        + f"\nCOOLING-OFF REFLECTION: {cooling_off.post_conversation_reflection}"
    )


async def run_strategy_judge(
    strategy: StrategyDefinition,
    turns: list[ConversationTurn],
    cooling_off: CoolingOff,
    mechanisms: list[dict],
) -> str:
    """
    Run the strategy-specific mechanism judge for one completed conversation.

    Returns a 2-3 sentence analysis grounded in the mechanism(s) the strategy
    was designed to activate, with evidence cited from the transcript.
    """
    async with _JUDGE_SEMAPHORE:
        client = anthropic.AsyncAnthropic(
            api_key=ANTHROPIC_API_KEY, max_retries=API_MAX_RETRIES
        )

        system = _build_system_prompt(strategy, mechanisms)
        transcript = _serialize_transcript(turns, cooling_off)

        user = (
            f"CONVERSATION TRANSCRIPT:\n{transcript}\n\n"
            "Write your 2-3 sentence mechanism analysis now."
        )

        message = await client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS_JUDGE,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text.strip()
