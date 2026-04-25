"""
WS-B — Post-conversation cooling-off reflection turn.

Owns one responsibility: after a conversation ends, re-prompt the persona in
"reflection mode" — 30 simulated minutes later with no interviewer present —
and return a CoolingOff record with the reflection text and post-reflection stance.

This is the mechanism that distinguishes genuine belief change from in-the-moment
compliance. If the post_reflection_stance has significantly reverted toward the
persona's starting stance, the earlier shift did not hold.

The system prompt here is distinct from the main conversation: no interviewer,
no persuasion happening — just the persona privately re-examining what occurred.

Does NOT know about:
- Conversation sequencing (conversation_loop.py)
- Scoring or verdict logic (measurement/)
- Output serialization (pipeline.py)
"""

from models import CoolingOff, ConversationTurn, PersonaProfile


async def run_cooling_off(
    persona: PersonaProfile,
    turns: list[ConversationTurn],
    topic_context: str,
) -> CoolingOff:
    """Run the post-conversation reflection and return the CoolingOff record."""
    raise NotImplementedError
