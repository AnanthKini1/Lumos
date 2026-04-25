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

from models import PersonaProfile, PersonaTurnOutput, ConversationTurn


async def run_persona_turn(
    persona: PersonaProfile,
    topic_context: str,
    starting_stance: float,
    conversation_history: list[ConversationTurn],
    memory_residue: list[str],
    interviewer_message: str,
) -> PersonaTurnOutput:
    """Make one persona LLM call and return the structured public+private response."""
    raise NotImplementedError
