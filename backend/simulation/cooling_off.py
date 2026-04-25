"""
WS-B — Post-conversation cooling-off reflection turn.

Distinct from the main conversation: no interviewer, no social pressure,
just the persona privately re-examining what occurred 30 simulated minutes later.

This is the mechanism that distinguishes genuine belief change from in-the-moment
compliance. If the post_reflection_stance reverts toward the starting stance,
the earlier shift did not hold.

Does NOT know about:
- Conversation sequencing (conversation_loop.py)
- Scoring or verdict logic (measurement/)
- Output serialization (pipeline.py)
"""

import anthropic

from config import ANTHROPIC_API_KEY, API_MAX_RETRIES, MAX_TOKENS_PERSONA, MODEL_ID
from models import CoolingOff, ConversationTurn, PersonaProfile

_COOLING_TOOL_NAME = "submit_cooling_off_reflection"

_COOLING_TOOL = {
    "name": _COOLING_TOOL_NAME,
    "description": "Submit your private post-conversation reflection.",
    "input_schema": {
        "type": "object",
        "properties": {
            "post_conversation_reflection": {
                "type": "string",
                "description": (
                    "Your honest private reflection, now that the conversation is over "
                    "and no one is listening. Fragmentary and personal, not a summary."
                ),
            },
            "post_reflection_stance": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 10.0,
                "description": "Where you actually stand now, privately, on a 0-10 scale.",
            },
        },
        "required": ["post_conversation_reflection", "post_reflection_stance"],
    },
}


def _compress_conversation(turns: list[ConversationTurn]) -> str:
    """Produce a brief summary of the conversation for the reflection context."""
    if not turns:
        return "You just had a brief conversation."

    lines = []
    for turn in turns:
        lines.append(
            f"Turn {turn.turn_number}: They said '{turn.persuader_message[:120]}'. "
            f"You said '{turn.persona_output.public_response[:100]}'. "
            f"(Private stance: {turn.persona_output.private_stance:.1f})"
        )
    return "\n".join(lines)


async def run_cooling_off(
    persona: PersonaProfile,
    turns: list[ConversationTurn],
    topic_context: str,
) -> CoolingOff:
    """Run the post-conversation reflection and return the CoolingOff record."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY, max_retries=API_MAX_RETRIES)

    system = f"""You are {persona.display_name}. {persona.first_person_description[:400]}

Thirty simulated minutes have passed since that conversation ended. The other person is gone. No one is watching or listening. You are alone with your thoughts.

Reflect privately on what just happened. What do you actually think now? Be honest with yourself — not with them, not with anyone. You are not performing for anyone.

Your reflection should be personal and unpolished — the way you actually think when no one is watching. Not a structured summary. Just your honest inner state."""

    conversation_summary = _compress_conversation(turns)
    final_stance = turns[-1].persona_output.private_stance if turns else 5.0

    user = (
        f"Here is what happened in the conversation:\n{conversation_summary}\n\n"
        f"Your private stance at the end of the conversation was {final_stance:.1f}/10.\n\n"
        f"Now that you've had some time alone — what do you actually think?\n"
        f"Use the {_COOLING_TOOL_NAME} tool to share your honest reflection."
    )

    response = await client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS_PERSONA,
        system=system,
        tools=[_COOLING_TOOL],
        tool_choice={"type": "tool", "name": _COOLING_TOOL_NAME},
        messages=[{"role": "user", "content": user}],
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise ValueError(f"Model did not invoke the tool. Response: {response.content}")
    return CoolingOff.model_validate(tool_block.input)
