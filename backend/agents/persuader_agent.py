"""
WS-B — Persuader agent: single LLM call per conversation turn.

Owns one responsibility: given a strategy's system prompt and the public-facing
conversation history so far, make one LLM call and return the persuader's
next message and an internal strategy note.

Critical constraint: the persuader ONLY sees public turns — it never receives
the persona's internal monologue, private stance, or emotional state. This
separation must be preserved here.

Responsibilities:
- Inject the strategy system prompt (loaded from StrategyDefinition)
- Fill the {TOPIC}, {TARGET_STANCE_DIRECTION}, {CONTEXT_BRIEFING} placeholders
- Build context from public-only conversation history
- Enforce the MAX_TOKENS_INTERVIEWER cap
- Parse and return the structured PersuaderOutput

Does NOT know about:
- Persona internals (persona_agent.py)
- Conversation sequencing (conversation_loop.py)
- Scoring or measurement (measurement/)
"""

import anthropic

from config import ANTHROPIC_API_KEY, API_MAX_RETRIES, MAX_TOKENS_INTERVIEWER, MODEL_ID
from models import ConversationTurn, PersuaderOutput, StrategyDefinition

_PERSUADER_TOOL_NAME = "submit_persuader_response"

_PERSUADER_TOOL = {
    "name": _PERSUADER_TOOL_NAME,
    "description": "Submit your next message and note your internal strategy reasoning.",
    "input_schema": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": (
                    "What you say to the person. Keep it concise — 1-3 sentences. "
                    "Do not lecture. Make it feel like a real conversation."
                ),
            },
            "internal_strategy_note": {
                "type": "string",
                "description": (
                    "One sentence describing what you were trying to do this turn "
                    "and why, for your own record."
                ),
            },
        },
        "required": ["message", "internal_strategy_note"],
    },
}

# The placeholders used in the strategy JSON system prompts
_TOPIC_PLACEHOLDER = "{TOPIC}"
_STANCE_PLACEHOLDER = "{TARGET_STANCE_DIRECTION}"
_CONTEXT_PLACEHOLDER = "{CONTEXT_BRIEFING}"


def _fill_strategy_prompt(
    raw_prompt: str,
    topic_display_name: str,
    target_stance_direction: str,
    context_briefing: str,
) -> str:
    return (
        raw_prompt
        .replace(_TOPIC_PLACEHOLDER, topic_display_name)
        .replace(_STANCE_PLACEHOLDER, target_stance_direction)
        .replace(_CONTEXT_PLACEHOLDER, context_briefing)
    )


def _build_conversation_context(public_history: list[ConversationTurn]) -> str:
    if not public_history:
        return "This is the opening of the conversation — you have not spoken yet."

    lines = ["CONVERSATION SO FAR (public exchanges only):"]
    for turn in public_history:
        lines.append(f"You: {turn.persuader_message}")
        lines.append(f"Person: {turn.persona_output.public_response}")
    return "\n".join(lines)


async def run_persuader_turn(
    strategy: StrategyDefinition,
    topic_context: str,
    public_history: list[ConversationTurn],
    topic_display_name: str = "",
    target_stance_direction: str = "a more open and flexible position on this issue",
) -> PersuaderOutput:
    """Make one persuader LLM call and return the next message."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY, max_retries=API_MAX_RETRIES)

    # Fill placeholders in the strategy's system prompt
    system_prompt = _fill_strategy_prompt(
        raw_prompt=strategy.persuader_system_prompt,
        topic_display_name=topic_display_name or topic_context[:80],
        target_stance_direction=target_stance_direction,
        context_briefing=topic_context,
    )

    # Cache the strategy system prompt — it's stable across all turns
    system_blocks = [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": (
                "\nKeep your message brief — 1 to 3 sentences maximum. "
                "Do not give speeches. Real persuasion happens in dialogue, not monologue. "
                "Use the submit_persuader_response tool to respond."
            ),
        },
    ]

    user_content = _build_conversation_context(public_history)

    response = await client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS_INTERVIEWER,
        system=system_blocks,
        tools=[_PERSUADER_TOOL],
        tool_choice={"type": "tool", "name": _PERSUADER_TOOL_NAME},
        messages=[{"role": "user", "content": user_content}],
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise ValueError(f"Model did not invoke the tool. Response: {response.content}")
    raw = tool_block.input

    # Ensure optional metadata field is present before validation
    if "internal_strategy_note" not in raw:
        raw = {**raw, "internal_strategy_note": ""}

    return PersuaderOutput.model_validate(raw)
