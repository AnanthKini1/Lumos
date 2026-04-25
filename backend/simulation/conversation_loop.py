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

from agents.persona_agent import run_persona_turn
from agents.persuader_agent import run_persuader_turn
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
    # (persona starts at starting_stance; persuader tries to move them
    #  toward the opposite end of the scale)
    scale = topic.stance_scale_definition
    if starting_stance >= 5.0:
        # Persona leans toward high end — persuader argues for the low end
        target_direction = scale.get("0", "the opposing position")
    else:
        # Persona leans toward low end — persuader argues for the high end
        target_direction = scale.get("10", "the opposing position")

    # Enrich context with key statistics when the topic provides them.
    # This appends to context_briefing so both agents see the same grounded data.
    topic_context = topic.context_briefing
    if topic.key_statistics:
        stats_lines = ["\n\nKEY STATISTICS (cite these when relevant):"]
        for s in topic.key_statistics:
            direction_note = f" [{s.direction}]" if s.direction else ""
            stats_lines.append(f"- {s.claim} (Source: {s.source}){direction_note}")
        topic_context += "\n".join(stats_lines)

    conversation_history: list[ConversationTurn] = []
    memory_residue: list[str] = []

    for turn_number in range(1, num_turns + 1):
        persuader_out = await run_persuader_turn(
            strategy=strategy,
            topic_context=topic_context,
            public_history=conversation_history,
            topic_display_name=topic.display_name,
            target_stance_direction=target_direction,
        )

        persona_out = await run_persona_turn(
            persona=persona,
            topic_context=topic_context,
            starting_stance=starting_stance,
            conversation_history=conversation_history,
            memory_residue=memory_residue,
            persuader_message=persuader_out.message,
            stance_scale=topic.stance_scale_definition,
        )

        turn = ConversationTurn(
            turn_number=turn_number,
            persuader_message=persuader_out.message,
            persuader_strategy_note=persuader_out.internal_strategy_note,
            persona_output=persona_out,
        )
        conversation_history.append(turn)

        if persona_out.memory_to_carry_forward.strip():
            memory_residue.append(persona_out.memory_to_carry_forward)

    return conversation_history
