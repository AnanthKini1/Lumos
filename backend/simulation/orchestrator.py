"""
WS-B — Async parallel orchestrator for multi-strategy simulation runs.

Owns one responsibility: given one persona, one topic, and a list of strategies,
launch one conversation_loop per strategy as a concurrent async task and collect
all results.

Each strategy's conversation is fully independent — they share no state. The same
persona starts each conversation from the same initial stance. Parallelism here is the primary tool for keeping wall-clock time manageable —
with 7 strategies each running 6 turns, sequential execution would be ~84 LLM
calls; parallel execution collapses this to ~12 sequential calls' worth of latency.

Does NOT know about:
- Individual turn logic (conversation_loop.py)
- Cooling-off or scoring (cooling_off.py, pipeline.py)
- Output serialization or file I/O (pipeline.py)
"""

from models import ConversationTurn, PersonaProfile, StrategyDefinition, TopicProfile


async def run_parallel_conversations(
    persona: PersonaProfile,
    topic: TopicProfile,
    strategies: list[StrategyDefinition],
    num_turns: int,
) -> dict[str, list[ConversationTurn]]:
    """
    Run all strategy conversations in parallel.
    Returns a mapping of strategy_id -> list[ConversationTurn].
    """
    raise NotImplementedError
