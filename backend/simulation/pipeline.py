"""
WS-B — End-to-end simulation pipeline. Top-level coordinator.

Owns one responsibility: given a scenario config (persona ID, topic ID, strategy
IDs), run the full simulation and write a complete SimulationOutput JSON file to
output/simulations/.

Execution order:
  1. Load persona, topic, and strategy profiles via data/loader.py
  2. Run all strategy conversations in parallel via orchestrator.py
  3. Run cooling-off for each strategy via cooling_off.py
  4. Score each conversation via measurement.scorer.score_conversation() — Seam 1
  5. Compute verdict for each via measurement.verdict.compute_verdict()
  6. Assemble StrategyOutcome records
  7. Generate overall synthesis via one summarizer LLM call
  8. Serialize the SimulationOutput to output/simulations/<scenario_id>.json

This is the ONLY module in the simulation package that imports from measurement/.
All other simulation modules are isolated from the measurement layer.

Does NOT know about:
- Individual turn logic (conversation_loop.py, agents/)
- How scoring works internally (measurement/)
- The HTTP layer (api/routes.py)
"""

from models import SimulationOutput


async def run_simulation(
    scenario_id: str,
    persona_id: str,
    topic_id: str,
    strategy_ids: list[str],
    num_turns: int = 6,
) -> SimulationOutput:
    """Run the full simulation and write results to disk. Returns the output."""
    raise NotImplementedError
