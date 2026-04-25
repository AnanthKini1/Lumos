"""
WS-B — FastAPI route handlers. Thin HTTP wrapper over the simulation pipeline.

Exposes three endpoints:
  POST /api/run        — trigger a new simulation run (accepts scenario config)
  GET  /api/scenarios  — list all cached scenario IDs in output/simulations/
  GET  /api/scenarios/{id} — retrieve a cached SimulationOutput by scenario ID

No business logic lives here. Each handler validates input, delegates to
simulation/pipeline.py or data/loader.py, and serializes the result.

The GET endpoints serve cached JSON — the frontend reads these at demo time.
The POST endpoint is used during development and for any live-mode toggle.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import OUTPUT_DIR
from simulation.pipeline import run_simulation
from models import SimulationOutput
import json

router = APIRouter()


class RunRequest(BaseModel):
    scenario_id: str
    persona_id: str
    topic_id: str
    strategy_ids: list[str]
    num_turns: int = 6


@router.post("/run", response_model=SimulationOutput)
async def trigger_run(request: RunRequest) -> SimulationOutput:
    """Trigger a new simulation run and return the result."""
    return await run_simulation(
        scenario_id=request.scenario_id,
        persona_id=request.persona_id,
        topic_id=request.topic_id,
        strategy_ids=request.strategy_ids,
        num_turns=request.num_turns,
    )


@router.get("/scenarios", response_model=list[str])
async def list_scenarios() -> list[str]:
    """Return all cached scenario IDs."""
    return [p.stem for p in OUTPUT_DIR.glob("*.json")]


@router.get("/scenarios/{scenario_id}", response_model=SimulationOutput)
async def get_scenario(scenario_id: str) -> SimulationOutput:
    """Retrieve a cached SimulationOutput by ID."""
    path = OUTPUT_DIR / f"{scenario_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return SimulationOutput.model_validate(json.loads(path.read_text()))
