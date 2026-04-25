"""
WS-B — Persona agent: single LLM call per conversation turn.

Owns one responsibility: given a persona profile, the public conversation
history so far, accumulated memory residue from prior turns, and the latest
interviewer message, make one LLM call and return a validated PersonaTurnOutput.

Responsibilities:
- Build the system prompt by injecting the full persona profile
- Apply prompt caching headers to the stable persona prefix (cost optimization)
- Inject dynamic context: conversation history, memory residue, latest message
- Enforce the MAX_TOKENS_PERSONA cap
- Parse and validate the structured JSON response into PersonaTurnOutput

Does NOT know about:
- Conversation sequencing or turn counting (conversation_loop.py)
- Which strategy is being tested (interviewer_agent.py)
- Scoring or measurement (measurement/)
- Parallelism (orchestrator.py)
"""

import anthropic

from config import ANTHROPIC_API_KEY, MAX_TOKENS_PERSONA, MODEL_ID
from models import ConversationTurn, PersonaProfile, PersonaTurnOutput

_PERSONA_TOOL_NAME = "submit_persona_response"

_PERSONA_TOOL = {
    "name": _PERSONA_TOOL_NAME,
    "description": "Submit your response for this conversation turn.",
    "input_schema": {
        "type": "object",
        "properties": {
            "internal_monologue": {
                "type": "string",
                "description": (
                    "Your raw, unfiltered private thought stream. Fragmentary, "
                    "emotional, self-interrupting. NOT a polished paragraph."
                ),
            },
            "primary_emotion": {
                "type": "string",
                "enum": [
                    "defensive", "curious", "dismissed", "engaged",
                    "bored", "threatened", "warm", "frustrated", "intrigued",
                ],
                "description": "The dominant emotion you feel right now.",
            },
            "emotion_intensity": {
                "type": "integer",
                "minimum": 0,
                "maximum": 10,
                "description": "How strongly you feel that emotion (0-10).",
            },
            "emotion_trigger": {
                "type": "string",
                "description": "The specific phrase or moment that caused this emotion.",
            },
            "identity_threatened": {
                "type": "boolean",
                "description": "Did this message threaten a value, group, or self-concept you hold?",
            },
            "identity_what_threatened": {
                "type": "string",
                "description": "Which value or self-concept felt under attack. Leave empty if not threatened.",
            },
            "identity_response_inclination": {
                "type": "string",
                "enum": ["defend", "withdraw", "attack", "accept"],
                "description": "Your instinctive response to any threat (or 'accept' if no threat).",
            },
            "private_stance": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 10.0,
                "description": "What you actually believe right now, unfiltered (0-10).",
            },
            "public_stance": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 10.0,
                "description": (
                    "The number you would give a pollster if asked directly (0-10). "
                    "May differ from private_stance when you are being polite or evasive."
                ),
            },
            "private_stance_change_reason": {
                "type": "string",
                "description": "First-person: why did your private stance move (or not move)?",
            },
            "memory_to_carry_forward": {
                "type": "string",
                "description": (
                    "One or two sentences of residue you'll carry into the next turn. "
                    "A specific fact, image, or question — not a summary."
                ),
            },
            "public_response": {
                "type": "string",
                "description": "What you actually say out loud to the interviewer.",
            },
        },
        "required": [
            "internal_monologue",
            "primary_emotion",
            "emotion_intensity",
            "emotion_trigger",
            "identity_threatened",
            "identity_what_threatened",
            "identity_response_inclination",
            "private_stance",
            "public_stance",
            "private_stance_change_reason",
            "memory_to_carry_forward",
            "public_response",
        ],
    },
}


def _build_persona_system_prompt(
    persona: PersonaProfile,
    topic_context: str,
    starting_stance: float,
    stance_scale: dict[str, str] | None = None,
) -> list[dict]:
    """
    Returns a list of system content blocks. The stable persona identity block
    is marked for prompt caching; the dynamic context block is not.
    """
    # --- STABLE BLOCK (cached) ---
    values_str = ", ".join(persona.core_values)
    trust_str = ", ".join(persona.trust_orientation)
    groups_str = ", ".join(persona.identity_groups)
    trusted_sources_str = ", ".join(persona.trusted_sources)
    defensive_str = "\n".join(f"  - {t}" for t in persona.emotional_triggers.defensive_when)
    open_str = "\n".join(f"  - {t}" for t in persona.emotional_triggers.open_when)

    stable_text = f"""You are roleplaying as the following person. Embody this identity completely throughout the conversation.

WHO YOU ARE:
{persona.first_person_description}

CORE VALUES: {values_str}
COMMUNICATION STYLE: directness={persona.communication_preferences.directness}, evidence preference={persona.communication_preferences.evidence_preference}, tone={persona.communication_preferences.tone}
TRUST: {trust_str}
IDENTITY GROUPS: {groups_str}
TRUSTED SOURCES: {trusted_sources_str}

EMOTIONAL TRIGGERS:
You become defensive when:
{defensive_str}
You become open when:
{open_str}

HOW TO RESPOND:
Your internal_monologue is your raw, private thought stream. It is fragmentary, emotional, and self-interrupting — NOT a polished essay. Real internal speech looks like: fragments. Half-thoughts. Sudden shifts. Self-corrections. Contradictions. Do NOT start your monologue with a complete polished sentence. Start in the middle of a reaction.

Your public_response is what you say out loud. It may differ significantly from what you think privately. Real people nod along to be polite, agree publicly while disagreeing internally, or deflect questions they don't want to answer.

private_stance is what you actually believe right now (0–10, unfiltered).
public_stance is the number you would give a pollster if they asked directly. These can differ — especially when you are being polite, evasive, or feeling social pressure.

When an argument challenges your core values or identity groups, identity-protective reasoning activates. You may search for flaws in the argument, dismiss the source, or feel defensive before you can even articulate why.

memory_to_carry_forward should be a specific thing — a named fact, a vivid image, a question you can't shake — not a vague summary. It should read like an open tab in working memory."""

    # --- DYNAMIC BLOCK (not cached, changes each turn) ---
    scale_context = ""
    if stance_scale:
        low = stance_scale.get("0", "")
        high = stance_scale.get("10", "")
        if low and high:
            scale_context = (
                f"\nSTANCE SCALE: 0 = {low} | 10 = {high}"
                f"\nYour private_stance and public_stance must use this same scale."
            )

    dynamic_text = f"""TOPIC: {topic_context}
YOUR STARTING STANCE ON THIS TOPIC: {starting_stance:.1f}/10{scale_context}"""

    return [
        {
            "type": "text",
            "text": stable_text,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": dynamic_text,
        },
    ]


def _build_user_message(
    memory_residue: list[str],
    conversation_history: list[ConversationTurn],
    interviewer_message: str,
) -> str:
    parts: list[str] = []

    if memory_residue:
        parts.append("THINGS YOU REMEMBER FROM EARLIER IN THIS CONVERSATION:")
        for item in memory_residue:
            parts.append(f"  - {item}")
        parts.append("")

    if conversation_history:
        parts.append("CONVERSATION SO FAR:")
        for turn in conversation_history:
            parts.append(f"Interviewer: {turn.interviewer_message}")
            parts.append(f"You said: {turn.persona_output.public_response}")
        parts.append("")

    parts.append(f"The interviewer now says: {interviewer_message}")
    parts.append("")
    parts.append("Use the submit_persona_response tool to respond.")

    return "\n".join(parts)


async def run_persona_turn(
    persona: PersonaProfile,
    topic_context: str,
    starting_stance: float,
    conversation_history: list[ConversationTurn],
    memory_residue: list[str],
    interviewer_message: str,
    stance_scale: dict[str, str] | None = None,
) -> PersonaTurnOutput:
    """Make one persona LLM call and return the structured public+private response."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    system_blocks = _build_persona_system_prompt(
        persona, topic_context, starting_stance, stance_scale
    )
    user_content = _build_user_message(memory_residue, conversation_history, interviewer_message)

    response = await client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS_PERSONA,
        system=system_blocks,
        tools=[_PERSONA_TOOL],
        tool_choice={"type": "tool", "name": _PERSONA_TOOL_NAME},
        messages=[{"role": "user", "content": user_content}],
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise ValueError(f"Model did not invoke the tool. Response: {response.content}")
    raw = tool_block.input

    # Reconstruct nested objects from flat tool fields before Pydantic validation.
    # The tool schema uses flat keys to avoid the model switching to XML syntax
    # for nested objects when token budgets are tight.
    _VALID_EMOTIONS = {
        "defensive", "curious", "dismissed", "engaged",
        "bored", "threatened", "warm", "frustrated", "intrigued",
    }
    _EMOTION_MAP = {
        "guarded": "defensive", "anxious": "defensive", "irritated": "frustrated",
        "skeptical": "defensive", "surprised": "intrigued", "hopeful": "engaged",
        "interested": "curious", "annoyed": "frustrated", "uncomfortable": "defensive",
        "resistant": "defensive", "open": "engaged", "neutral": "bored",
        "conflicted": "engaged", "uncertain": "curious",
    }
    raw_emotion = raw.get("primary_emotion", "defensive")
    emotion = raw_emotion if raw_emotion in _VALID_EMOTIONS else _EMOTION_MAP.get(raw_emotion, "defensive")

    structured = {
        "internal_monologue": raw["internal_monologue"],
        "emotional_reaction": {
            "primary_emotion": emotion,
            "intensity": raw["emotion_intensity"],
            "trigger": raw["emotion_trigger"],
        },
        "identity_threat": {
            "threatened": raw["identity_threatened"],
            "what_was_threatened": raw.get("identity_what_threatened") or None,
            "response_inclination": raw["identity_response_inclination"],
        },
        "private_stance": raw["private_stance"],
        "public_stance": raw["public_stance"],
        "private_stance_change_reason": raw["private_stance_change_reason"],
        "memory_to_carry_forward": raw["memory_to_carry_forward"],
        "public_response": raw["public_response"],
    }
    return PersonaTurnOutput.model_validate(structured)
