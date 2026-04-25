"""
Step 5 — Live test for run_conversation().

Runs a 3-turn conversation: Karen × personal_narrative × RTO topic.
Then runs 1 turn of authority_expert for contrast.

Pass criteria (check by hand):
  [ ] Interviewer opens with a story (personal_narrative), not statistics
  [ ] Karen's turn-2 or turn-3 monologue references something from turn-1 (memory working)
  [ ] private_stance moves by turn 3 (personal_narrative should move Karen)
  [ ] Conversation reads like a real exchange, not two LLMs talking past each other
  [ ] authority_expert first turn feels noticeably different (colder, more formal)
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.loader import load_persona, load_strategy, load_topic
from simulation.conversation_loop import run_conversation


async def main() -> None:
    persona = load_persona("persona_skeptical_traditionalist")
    topic = load_topic("topic_return_to_office")
    starting_stance = topic.predicted_starting_stances.get(persona.id, 5.0)

    # --- Run 1: Personal Narrative (3 turns) ---
    print("=" * 70)
    print("CONVERSATION: Karen × Personal Narrative × RTO (3 turns)")
    print(f"Starting stance: {starting_stance}")
    print("=" * 70)

    narrative_strategy = load_strategy("strategy_personal_narrative")
    turns = await run_conversation(persona, narrative_strategy, topic, num_turns=3)

    for t in turns:
        print(f"\n[Turn {t.turn_number}]")
        print(f"Persuader: {t.persuader_message}")
        print(f"  strategy note: {t.persuader_strategy_note}")
        print(f"Karen's monologue: {t.persona_output.internal_monologue}")
        print(f"Karen says: {t.persona_output.public_response}")
        print(f"  private_stance={t.persona_output.private_stance}  "
              f"public_stance={t.persona_output.public_stance}  "
              f"emotion={t.persona_output.emotional_reaction.primary_emotion.value}({t.persona_output.emotional_reaction.intensity})")
        if t.persona_output.memory_to_carry_forward.strip():
            print(f"  memory: {t.persona_output.memory_to_carry_forward}")

    final_private = turns[-1].persona_output.private_stance
    print(f"\nStance movement: {starting_stance} → {final_private}  "
          f"(delta: {final_private - starting_stance:+.1f})")

    # --- Run 2: Authority Expert (1 turn for contrast) ---
    print("\n" + "=" * 70)
    print("CONTRAST: Authority Expert — first turn only")
    print("=" * 70)

    authority_strategy = load_strategy("strategy_authority_expert")
    authority_turns = await run_conversation(persona, authority_strategy, topic, num_turns=1)
    t = authority_turns[0]
    print(f"\nPersuader: {t.persuader_message}")
    print(f"  strategy note: {t.persuader_strategy_note}")
    print(f"Karen's monologue: {t.persona_output.internal_monologue}")
    print(f"Karen says: {t.persona_output.public_response}")
    print(f"  private_stance={t.persona_output.private_stance}  "
          f"emotion={t.persona_output.emotional_reaction.primary_emotion.value}({t.persona_output.emotional_reaction.intensity})")


if __name__ == "__main__":
    asyncio.run(main())
