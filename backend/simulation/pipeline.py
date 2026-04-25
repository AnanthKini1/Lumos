"""
WS-B — End-to-end simulation pipeline. Top-level coordinator.

Owns one responsibility: given a scenario config (persona ID, topic ID), run
ALL configured strategies against the persona and write a complete SimulationOutput
to output/simulations/.

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
    num_turns: int = 6,
) -> SimulationOutput:
    """
    Run the full simulation against ALL configured strategies and write results to disk.
    Strategies are loaded automatically from data/strategies/ — no selection needed.
    Returns the complete SimulationOutput.
    """
    raise NotImplementedError
