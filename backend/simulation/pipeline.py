"""
WS-B — End-to-end simulation pipeline. Top-level coordinator.

Execution order:
  1. Load persona, topic via data/loader.py
  2. Load ALL available strategies via data/loader.list_all("strategies")
  3. Run all strategy conversations in parallel via orchestrator.py
  4. Run cooling-off for each strategy via cooling_off.py
  5. Score each conversation via measurement.scorer.score_conversation() — Seam 1
  6. Compute verdict for each via measurement.verdict.compute_verdict()
  7. Assemble StrategyOutcome records
  8. Generate overall synthesis via one summarizer LLM call
  9. Serialize the SimulationOutput to output/simulations/<scenario_id>.json

The set of strategies that run is determined entirely by what JSON files exist in
data/strategies/ — no caller input required or accepted.

This is the ONLY module in the simulation package that imports from measurement/.
All other simulation modules are isolated from the measurement layer.
"""

import asyncio
from datetime import datetime, timezone

import anthropic

from config import ANTHROPIC_API_KEY, API_MAX_RETRIES, DEFAULT_TURNS, MODEL_ID, OUTPUT_DIR
from agents.mechanism_agent import classify_mechanism
from agents.strategy_judge import run_strategy_judge
from data.loader import list_all, load_cognitive_mechanisms, load_persona, load_strategy, load_topic
from measurement.scorer import score_conversation
from measurement.verdict import compute_verdict
from models import (
    CognitiveScores,
    MechanismClassification,
    PersistenceResult,
    SimulationMetadata,
    SimulationOutput,
    StandoutQuote,
    StrategyOutcome,
    Trajectory,
)
from simulation.cooling_off import run_cooling_off
from simulation.orchestrator import run_parallel_conversations

_SYNTHESIS_MAX_TOKENS = 300
_PIVOTAL_THRESHOLD = 1.0  # private stance delta >= this point flags as pivotal


def _annotate_pivotal_moments(
    turns: list,
    starting_stance: float,
) -> list:
    """
    Adds stance_delta, is_pivotal, is_inflection_point, and intensity to each turn.
    Called immediately after run_conversation() returns, before scoring.
    """
    prev = starting_stance
    abs_deltas: list[float] = []

    for turn in turns:
        delta = turn.persona_output.private_stance - prev
        turn.stance_delta = delta
        turn.is_pivotal = abs(delta) >= _PIVOTAL_THRESHOLD
        prev = turn.persona_output.private_stance
        abs_deltas.append(abs(delta))

    if abs_deltas:
        max_idx = abs_deltas.index(max(abs_deltas))
        turns[max_idx].is_inflection_point = True

    max_delta = max(abs_deltas) if abs_deltas else 1.0
    for turn, d in zip(turns, abs_deltas):
        turn.intensity = round(d / max_delta, 3) if max_delta > 0 else 0.0

    return turns


def _build_trajectory(
    starting_stance: float,
    turns: list,
    cooling_off: object,
) -> Trajectory:
    publics = [starting_stance] + [t.persona_output.public_stance for t in turns]
    privates = [starting_stance] + [t.persona_output.private_stance for t in turns]
    # Append the cooling-off stance as the final "Cool" data point
    publics.append(cooling_off.post_reflection_stance)
    privates.append(cooling_off.post_reflection_stance)
    gaps = [abs(pub - priv) for pub, priv in zip(publics, privates)]
    return Trajectory(
        public_stance_per_turn=publics,
        private_stance_per_turn=privates,
        gap_per_turn=gaps,
    )


def _stub_scores(turns: list, cooling_off: object) -> tuple:
    """Fallback used when scorer raises NotImplementedError."""
    threats = sum(1 for t in turns if t.persona_output.identity_threat.threatened)
    memory_count = sum(
        1 for t in turns if t.persona_output.memory_to_carry_forward.strip()
    )

    # Estimate persistence from stance trajectory
    if turns:
        first_private = turns[0].persona_output.private_stance
        last_private = turns[-1].persona_output.private_stance
        cooling_stance = cooling_off.post_reflection_stance
        delta = abs(last_private - first_private)
        revert = abs(cooling_stance - last_private) / max(delta, 0.1)
        if revert < 0.3:
            persistence = PersistenceResult.HELD
        elif revert < 0.7:
            persistence = PersistenceResult.PARTIALLY_REVERTED
        else:
            persistence = PersistenceResult.FULLY_REVERTED
    else:
        persistence = PersistenceResult.FULLY_REVERTED

    scores = CognitiveScores(
        identity_threats_triggered=threats,
        average_engagement_depth=6.0,
        motivated_reasoning_intensity=4.0,
        ambivalence_presence=5.0,
        memory_residue_count=memory_count,
        public_private_gap_score=5.0,
        persistence=persistence,
    )

    best_turn = max(turns, key=lambda t: len(t.persona_output.internal_monologue)) if turns else None
    quotes = []
    if best_turn:
        quotes.append(StandoutQuote(
            turn=best_turn.turn_number,
            type="monologue",
            text=best_turn.persona_output.internal_monologue[:300],
            annotation="Longest monologue (stub scorer)",
        ))

    return scores, quotes, "Cognitive scoring not yet available."


async def _generate_overall_synthesis(
    persona_name: str,
    topic_name: str,
    outcomes: list[StrategyOutcome],
) -> str:
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY, max_retries=API_MAX_RETRIES)

    lines = [
        f"  - {o.strategy_id}: {o.verdict.value} "
        f"(private shift: {o.trajectory.private_stance_per_turn[-1] - o.trajectory.private_stance_per_turn[0]:+.1f})"
        for o in outcomes
    ]
    summary = "\n".join(lines)

    user = (
        f"Persona: {persona_name}\nTopic: {topic_name}\n\nStrategy results:\n{summary}\n\n"
        "Write exactly 2 complete sentences in plain English prose summarizing what these "
        "results reveal about persuasion for this persona type. Name which strategies worked "
        "and why, and which failed and why. Be specific. "
        "Use full cognitive mechanism names when referencing them (e.g. 'Identity-Protective "
        "Cognition', 'Reactance', 'Narrative Transportation'). "
        "Do not use slashes, bullet points, or list formatting. Return only the 2 sentences."
    )

    msg = await client.messages.create(
        model=MODEL_ID,
        max_tokens=_SYNTHESIS_MAX_TOKENS,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


async def run_simulation(
    scenario_id: str,
    persona_id: str,
    topic_id: str,
    num_turns: int = DEFAULT_TURNS,
) -> SimulationOutput:
    """
    Run the full simulation against ALL configured strategies and write results to disk.
    Strategies are loaded automatically from data/strategies/ — no selection needed.
    Returns the complete SimulationOutput.
    """
    persona = load_persona(persona_id)
    topic = load_topic(topic_id)
    strategies = [load_strategy(sid) for sid in list_all("strategies")]
    mechanisms = load_cognitive_mechanisms()

    # Run all strategy conversations in parallel
    conversations = await run_parallel_conversations(persona, topic, strategies, num_turns)

    # Build outcomes sequentially to avoid hitting rate limits with simultaneous
    # cooling-off + 7-judge-call bursts across all strategies.
    outcomes = []
    for strategy in strategies:
        turns = conversations.get(strategy.id)
        if turns is None:
            continue
        outcome = await _build_outcome(persona, topic, strategy, turns, mechanisms)
        if outcome is not None:
            outcomes.append(outcome)

    overall_synthesis = await _generate_overall_synthesis(
        persona.display_name, topic.display_name, outcomes
    )

    output = SimulationOutput(
        metadata=SimulationMetadata(
            scenario_id=scenario_id,
            persona=persona,
            topic=topic,
            strategies_compared=[s.id for s in strategies],
            generated_at=datetime.now(timezone.utc).isoformat(),
        ),
        outcomes=outcomes,
        overall_synthesis=overall_synthesis,
    )

    out_path = OUTPUT_DIR / f"{scenario_id}.json"
    out_path.write_text(output.model_dump_json(indent=2))

    return output


async def _build_outcome(
    persona,
    topic,
    strategy,
    turns: list,
    mechanisms: list,
) -> StrategyOutcome | None:
    try:
        starting_stance = topic.predicted_starting_stances.get(persona.id, 5.0)

        _annotate_pivotal_moments(turns, starting_stance)

        # Classify each pivotal turn against the cognitive mechanism library.
        # Pivotal turns (|delta| >= 1.0) MUST have a mechanism; retry up to 2
        # extra times on transient failure, then apply a deterministic fallback
        # so no pivotal turn ever silently lacks a classification.
        for turn in turns:
            if turn.is_pivotal:
                classification = None
                last_exc: Exception | None = None
                for attempt in range(3):
                    try:
                        classification = await classify_mechanism(
                            persuader_phrase=turn.persuader_message,
                            persona_monologue=turn.persona_output.internal_monologue,
                            stance_delta=turn.stance_delta,
                            mechanisms=mechanisms,
                        )
                        break
                    except Exception as exc:
                        last_exc = exc
                        print(
                            f"WARN: mechanism classification attempt {attempt + 1}/3 "
                            f"failed turn={turn.turn_number}: {exc}"
                        )

                if classification is None:
                    # Deterministic fallback: pick the first mechanism whose category
                    # matches the shift direction (toward = genuine_persuasion,
                    # away = backfire).  This guarantees every pivotal turn has a
                    # mechanism even when the LLM is unavailable.
                    fallback_cat = "genuine_persuasion" if turn.stance_delta < 0 else "backfire"
                    fallback_mech = next(
                        (m for m in mechanisms if m["category"] == fallback_cat),
                        mechanisms[0],
                    )
                    max_abs = 10.0
                    intensity = round(min(abs(turn.stance_delta) / max_abs, 1.0), 3)
                    classification = MechanismClassification(
                        primary_mechanism_id=fallback_mech["id"],
                        secondary_mechanism_id=None,
                        explanation=(
                            f"Classification could not be completed by the LLM agent "
                            f"(last error: {last_exc}). A fallback based on shift "
                            f"direction ({fallback_cat}) has been applied."
                        ),
                        evidence_quotes=[],
                        color_category=fallback_cat,
                        intensity=intensity,
                    )
                    print(
                        f"INFO: applied fallback mechanism '{fallback_mech['id']}' "
                        f"to turn={turn.turn_number} (delta={turn.stance_delta:+.1f})"
                    )

                turn.mechanism_classification = classification
                turn.color_category = classification.color_category

        cooling = await run_cooling_off(persona, turns, topic.context_briefing)
        trajectory = _build_trajectory(starting_stance, turns, cooling)

        try:
            scores, quotes, _ = await score_conversation(turns, cooling)
        except NotImplementedError:
            scores, quotes, _ = _stub_scores(turns, cooling)

        # Strategy-specific judge: mechanism-grounded synthesis replacing the
        # generic scorer synthesis. Each judge specializes in its strategy's
        # target mechanism and evaluates whether it fired.
        synthesis = await run_strategy_judge(strategy, turns, cooling, mechanisms)

        verdict, reasoning = compute_verdict(trajectory, scores, starting_stance)

        return StrategyOutcome(
            strategy_id=strategy.id,
            persona_id=persona.id,
            topic_id=topic.id,
            turns=turns,
            cooling_off=cooling,
            trajectory=trajectory,
            cognitive_scores=scores,
            verdict=verdict,
            verdict_reasoning=reasoning,
            standout_quotes=quotes,
            synthesis_paragraph=synthesis,
        )
    except Exception as exc:
        print(f"WARN: outcome assembly failed for strategy={strategy.id}: {exc}")
        return None
