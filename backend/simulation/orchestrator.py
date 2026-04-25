"""
WS-B — Async parallel orchestrator for multi-strategy simulation runs.

Launches one conversation_loop per strategy as a concurrent async task.
Each strategy's conversation is fully independent — they share no state.
The same persona starts each conversation from the same initial stance.

Parallelism collapses wall-clock time from ~84 sequential LLM calls (7 strategies
× 6 turns × 2 agents) to roughly 12 sequential calls' worth of latency.

Does NOT know about:
- Individual turn logic (conversation_loop.py)
- Cooling-off or scoring (cooling_off.py, pipeline.py)
- Output serialization or file I/O (pipeline.py)
"""

import asyncio

from models import ConversationTurn, PersonaProfile, StrategyDefinition, TopicProfile
from simulation.conversation_loop import run_conversation


async def _safe_run(
    persona: PersonaProfile,
    strategy: StrategyDefinition,
    topic: TopicProfile,
    num_turns: int,
) -> tuple[str, list[ConversationTurn] | None]:
    try:
        turns = await run_conversation(persona, strategy, topic, num_turns)
        return strategy.id, turns
    except Exception as exc:
        print(f"WARN: conversation failed for strategy={strategy.id}: {exc}")
        return strategy.id, None


async def run_parallel_conversations(
    persona: PersonaProfile,
    topic: TopicProfile,
    strategies: list[StrategyDefinition],
    num_turns: int,
) -> dict[str, list[ConversationTurn]]:
    """
    Run all strategy conversations in parallel.
    Returns a mapping of strategy_id -> list[ConversationTurn].
    Failed conversations are silently dropped from the result.
    """
    results = await asyncio.gather(
        *[_safe_run(persona, s, topic, num_turns) for s in strategies]
    )
    return {sid: turns for sid, turns in results if turns is not None}
