"""
Step 4 — Live test for run_persona_turn().

Calls run_persona_turn() 5 times for persona_skeptical_traditionalist (Karen) on
topic_return_to_office and prints all outputs for manual review.

Pass criteria (check by hand):
  [ ] internal_monologue is fragmentary — NOT a polished paragraph
  [ ] Feels like Karen (small-town, traditionalist, warm but guarded)
  [ ] private_stance near 7.0 (starting position, slight defensiveness)
  [ ] public_response politely engaged but non-committal
  [ ] At least some gap between monologue and public response
  Bar: 4/5 feel authentically human. If hollow, iterate system prompt.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.persona_agent import run_persona_turn
from data.loader import load_persona, load_topic

_OPENING_MESSAGE = (
    "I think people who work from home are just avoiding accountability. "
    "Offices exist for a reason."
)


async def main() -> None:
    persona = load_persona("persona_skeptical_traditionalist")
    topic = load_topic("topic_return_to_office")
    starting_stance = topic.predicted_starting_stances.get(persona.id, 5.0)

    print(f"Persona : {persona.display_name}")
    print(f"Topic   : {topic.display_name}")
    print(f"Starting stance: {starting_stance}")
    print(f"Message : {_OPENING_MESSAGE}\n")
    print("=" * 70)

    monologues = []
    for i in range(5):
        print(f"\n--- Run {i + 1} ---")
        out = await run_persona_turn(
            persona=persona,
            topic_context=topic.context_briefing,
            starting_stance=starting_stance,
            conversation_history=[],
            memory_residue=[],
            persuader_message=_OPENING_MESSAGE,
        )
        monologues.append(out.internal_monologue)
        print(f"internal_monologue : {out.internal_monologue}")
        print(f"emotional_reaction : {out.emotional_reaction.primary_emotion} "
              f"(intensity {out.emotional_reaction.intensity}/10)")
        print(f"private_stance     : {out.private_stance}")
        print(f"public_stance      : {out.public_stance}  "
              f"(gap: {abs(out.public_stance - out.private_stance):.1f})")
        print(f"public_response    : {out.public_response}")

    print("\n" + "=" * 70)
    print("MONOLOGUE COMPARISON (all 5 side by side):\n")
    for i, m in enumerate(monologues, 1):
        print(f"[{i}] {m}\n")


if __name__ == "__main__":
    asyncio.run(main())
