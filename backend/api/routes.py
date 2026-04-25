"""
WS-B — FastAPI route handlers. Thin HTTP wrapper over the simulation pipeline.

Exposes three endpoints:
  POST /api/run        — trigger a new simulation run (persona + topic only;
                         all configured strategies run automatically)
  GET  /api/scenarios  — list all cached scenario IDs in output/simulations/
  GET  /api/scenarios/{id} — retrieve a cached SimulationOutput by scenario ID

No business logic lives here. Each handler validates input, delegates to
simulation/pipeline.py or data/loader.py, and serializes the result.

The GET endpoints serve cached JSON — the frontend reads these at demo time.
The POST endpoint is used during development and for any live-mode toggle.
Strategy selection does NOT happen here — pipeline.py auto-loads all strategies.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import OUTPUT_DIR
from data.loader import load_persona, load_topic, load_strategy, list_all
from simulation.pipeline import run_simulation
from models import PersonaProfile, StrategyDefinition, TopicProfile, SimulationOutput
import json

router = APIRouter()


class RunRequest(BaseModel):
    scenario_id: str
    persona_id: str
    topic_id: str
    num_turns: int = 6


@router.post("/run", response_model=SimulationOutput)
async def trigger_run(request: RunRequest) -> SimulationOutput:
    """Trigger a new simulation run against all configured strategies."""
    return await run_simulation(
        scenario_id=request.scenario_id,
        persona_id=request.persona_id,
        topic_id=request.topic_id,
        num_turns=request.num_turns,
    )


@router.get("/personas", response_model=list[PersonaProfile])
async def list_personas() -> list[PersonaProfile]:
    """Return all persona profiles."""
    return [load_persona(pid) for pid in sorted(list_all("personas"))]


@router.get("/topics", response_model=list[TopicProfile])
async def list_topics() -> list[TopicProfile]:
    """Return all topic profiles."""
    return [load_topic(tid) for tid in sorted(list_all("topics"))]


@router.get("/strategies", response_model=list[StrategyDefinition])
async def list_strategies() -> list[StrategyDefinition]:
    """Return all strategy definitions."""
    return [load_strategy(sid) for sid in sorted(list_all("strategies"))]


@router.get("/catalog")
async def get_catalog() -> dict:
    """Return full catalog: all personas, topics, strategies in one call."""
    return {
        "personas": [load_persona(pid) for pid in sorted(list_all("personas"))],
        "topics": [load_topic(tid) for tid in sorted(list_all("topics"))],
        "strategies": [load_strategy(sid) for sid in sorted(list_all("strategies"))],
    }


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
