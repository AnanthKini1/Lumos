"""
WS-B — Single conversation runner for one (persona, strategy, topic) triple.

Owns one responsibility: run a complete multi-turn conversation from start to
finish and return the ordered list of ConversationTurn records.

Turn sequencing:
  1. Interviewer agent produces a message (sees only public history)
  2. Persona agent receives message + accumulated memory residue, produces response
  3. Persona's memory_to_carry_forward is accumulated for subsequent turns
  4. Repeat for DEFAULT_TURNS turns (or until a termination condition)

Critical invariant: the persona's raw internal monologue from prior turns must
NEVER be injected back into the persona's context. Only the public conversation
history and the distilled memory_to_carry_forward accumulation are passed in.

Does NOT know about:
- Running multiple strategies in parallel (orchestrator.py)
- The cooling-off reflection turn (cooling_off.py)
- Scoring or output serialization (pipeline.py)
"""

from models import ConversationTurn, PersonaProfile, StrategyDefinition, TopicProfile


async def run_conversation(
    persona: PersonaProfile,
    strategy: StrategyDefinition,
    topic: TopicProfile,
    num_turns: int,
) -> list[ConversationTurn]:
    """Run a full multi-turn conversation and return all turns."""
    raise NotImplementedError
