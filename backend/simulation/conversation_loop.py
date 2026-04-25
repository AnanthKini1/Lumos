"""
WS-B — Single conversation runner for one (persona, strategy, topic) triple.

Turn sequencing:
  1. Interviewer agent produces a message (sees only public history)
  2. Persona agent receives message + accumulated memory residue, produces response
  3. Persona's memory_to_carry_forward is accumulated for subsequent turns
  4. Repeat for num_turns turns

Critical invariant: the persona's raw internal monologue from prior turns must
NEVER be injected back into the persona's context. Only the public conversation
history and the distilled memory_to_carry_forward accumulation are passed in.

Does NOT know about:
- Running multiple strategies in parallel (orchestrator.py)
- The cooling-off reflection turn (cooling_off.py)
- Scoring or output serialization (pipeline.py)
"""

from agents.interviewer_agent import run_interviewer_turn
from agents.persona_agent import run_persona_turn
from models import ConversationTurn, PersonaProfile, StrategyDefinition, TopicProfile


async def run_conversation(
    persona: PersonaProfile,
    strategy: StrategyDefinition,
    topic: TopicProfile,
    num_turns: int,
) -> list[ConversationTurn]:
    """Run a full multi-turn conversation and return all turns."""
    starting_stance = topic.predicted_starting_stances.get(persona.id, 5.0)

    # Derive a human-readable target direction from the stance scale
    # (persona starts at starting_stance; interviewer tries to move them
    #  toward the opposite end of the scale)
    scale = topic.stance_scale_definition
    if starting_stance >= 5.0:
        # Persona leans toward high end — interviewer argues for the low end
        target_direction = scale.get("0", "the opposing position")
    else:
        # Persona leans toward low end — interviewer argues for the high end
        target_direction = scale.get("10", "the opposing position")

    conversation_history: list[ConversationTurn] = []
    memory_residue: list[str] = []

    for turn_number in range(1, num_turns + 1):
        interviewer_out = await run_interviewer_turn(
            strategy=strategy,
            topic_context=topic.context_briefing,
            public_history=conversation_history,
            topic_display_name=topic.display_name,
            target_stance_direction=target_direction,
        )

        persona_out = await run_persona_turn(
            persona=persona,
            topic_context=topic.context_briefing,
            starting_stance=starting_stance,
            conversation_history=conversation_history,
            memory_residue=memory_residue,
            interviewer_message=interviewer_out.message,
            stance_scale=topic.stance_scale_definition,
        )

        turn = ConversationTurn(
            turn_number=turn_number,
            interviewer_message=interviewer_out.message,
            interviewer_strategy_note=interviewer_out.internal_strategy_note,
            persona_output=persona_out,
        )
        conversation_history.append(turn)

        if persona_out.memory_to_carry_forward.strip():
            memory_residue.append(persona_out.memory_to_carry_forward)

    return conversation_history
