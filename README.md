# Lumos — Internal Mind Simulator

An AI simulation that models the interior cognition of a person being persuaded. Shows not just whether stance changes, but what's actually happening inside the mind as it does (or doesn't).

Built for Hacktech 2026 · Listen Labs "Simulate Humanity" track.

---

## Workstream Ownership

| Module | Owner | Description |
|---|---|---|
| `backend/data/` (JSON files) | WS-A | Personas, strategies, topics |
| `backend/measurement/` | WS-A | Judge prompts, scorer, verdict logic |
| `backend/agents/` | WS-B | Persona and interviewer LLM calls |
| `backend/simulation/` | WS-B | Conversation loop, orchestrator, pipeline |
| `backend/api/` | WS-B | FastAPI routes |
| `frontend/` | WS-C | All UI — setup, mind viewer, report |

**Shared / locked** (coordinate before changing):
- `backend/models.py` — Pydantic schemas
- `frontend/src/types/simulation.ts` — TypeScript interfaces
- `backend/data/loader.py` — data loading utilities
- `backend/measurement/scorer.py:score_conversation()` — the WS-B/WS-A seam

---

## Setup

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
python main.py
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## Architecture in one paragraph

WS-B's `pipeline.py` runs all strategy conversations in parallel via `orchestrator.py`, each using `conversation_loop.py` to alternate between `interviewer_agent.py` and `persona_agent.py`. After each conversation, `cooling_off.py` runs a reflection turn. The full transcript passes to WS-A's `scorer.py` (the only cross-workstream code call), which runs judge LLM calls per cognitive dimension. `verdict.py` applies deterministic rules to produce a categorical verdict. The final `SimulationOutput` is serialized to `output/simulations/` and the frontend reads it directly — no API call at demo time.
