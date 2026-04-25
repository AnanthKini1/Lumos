"""
WS-B — Interviewer agent: single LLM call per conversation turn.

Owns one responsibility: given a strategy's system prompt and the public-facing
conversation history so far, make one LLM call and return the interviewer's
next message and an internal strategy note.

Critical constraint: the interviewer ONLY sees public turns — it never receives
the persona's internal monologue, private stance, or emotional state. This
separation must be preserved here.

Responsibilities:
- Inject the strategy system prompt (loaded from StrategyDefinition)
- Build context from public-only conversation history
- Enforce the MAX_TOKENS_INTERVIEWER cap
- Parse and return the structured InterviewerOutput

Does NOT know about:
- Persona internals (persona_agent.py)
- Conversation sequencing (conversation_loop.py)
- Scoring or measurement (measurement/)
"""

from models import ConversationTurn, InterviewerOutput, StrategyDefinition


async def run_interviewer_turn(
    strategy: StrategyDefinition,
    topic_context: str,
    public_history: list[ConversationTurn],
) -> InterviewerOutput:
    """Make one interviewer LLM call and return the next message."""
    raise NotImplementedError
