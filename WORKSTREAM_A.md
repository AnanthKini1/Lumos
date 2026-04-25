# Workstream A: Data, Personas, Strategies & Measurement
## Feature Checklist

Mark completed items with [x]. Check this file at the start of every feature.

---

## WHAT THE TEAM HAS ALREADY BUILT (do not touch without sync)

- `backend/models.py` — Pydantic models for ALL shared contracts. This is the schema source of truth. No separate schema files needed.
- `backend/config.py` — all file paths. Data lives in `backend/data/`, output in `backend/output/simulations/`.
- `backend/data/loader.py` — load_persona(), load_strategy(), load_topic() already implemented.
- `backend/measurement/judge_prompts.py` — stubbed. WS-A fills in the prompt strings.
- `backend/measurement/judge_agent.py` — stubbed. WS-A implements run_judge_call().
- `backend/measurement/scorer.py` — stubbed. WS-A implements score_conversation().
- `backend/measurement/verdict.py` — stubbed with thresholds defined. WS-A implements compute_verdict().
- `frontend/src/data/mock_simulation.json` — complete, high-quality mock already written by frontend team.

---

## PHASE 0 — Setup & Mock Output

- [x] **A0.1** Directory structure exists: `backend/data/personas/`, `backend/data/strategies/`, `backend/data/topics/`, `backend/output/simulations/` (created by team via config.py)
- [x] **A0.2** Mock SimulationOutput JSON — `frontend/src/data/mock_simulation.json` already written by frontend team. Complete with 2 strategies (GENUINE_BELIEF_SHIFT + BACKFIRE), 3 turns each, cooling-off, cognitive scores, standout quotes, synthesis paragraphs.

---

## PHASE 1 — Schema Validation

- [x] **A1.1** Review `backend/models.py` — confirmed all fields match Shared Contracts. Key notes: `PersonaProfile` has no `initial_stances` (use `TopicProfile.predicted_starting_stances`). `CognitiveScores` includes `public_private_gap_score` and `persistence: PersistenceResult`. No structural changes needed.

---

## PHASE 1 — Schema Validation

- [x] **A1.2** Write `backend/validate_data.py` — loads every JSON in `backend/data/` via loader.py (which uses Pydantic model_validate). Prints pass/fail per file. Run after every new data file.
- [x] **A1.3** Write seed persona `backend/data/personas/persona_skeptical_traditionalist.json` — use mock_simulation.json's persona object as reference for field values and tone. Validate passes.

---

## PHASE 2 — Persona Roster (8 personas)

All files go in `backend/data/personas/`. Run `python backend/validate_data.py` after each.

- [x] **A2.1** `persona_skeptical_traditionalist.json` — Pew Faith & Flag Conservatives + VALS Believers (from A1.3, confirm complete)
- [x] **A2.2** `persona_progressive_urban.json` — Pew Progressive Left + Hidden Tribes Progressive Activists
- [x] **A2.3** `persona_pragmatic_moderate.json` — Pew Establishment Liberals + VALS Achievers
- [x] **A2.4** `persona_disengaged_skeptic.json` — Hidden Tribes Passive Liberals + Pew Stressed Sideliners
- [x] **A2.5** `persona_faith_community_anchor.json` — Pew Committed Conservatives + VALS Believers
- [x] **A2.6** `persona_ambitious_achiever.json` — VALS Achievers + Pew Enterprisers
- [x] **A2.7** `persona_empathic_helper.json` — VALS Experiencers/Makers + Hidden Tribes Traditional Liberals
- [x] **A2.8** `persona_analytical_thinker.json` — Forrester Technographics Empowered + VALS Thinkers
- [ ] **A2.9** All 8 pass `validate_data.py`

Each persona JSON must have (matching PersonaProfile Pydantic model exactly):
- `id`, `display_name`, `demographic_shorthand`
- `first_person_description` — 2-3 paragraphs, first person, injectable into system prompt
- `core_values` (list of strings)
- `communication_preferences` — `{directness, evidence_preference, tone}`
- `trust_orientation` (list)
- `identity_groups` (list)
- `emotional_triggers` — `{defensive_when: [...], open_when: [...]}`
- `trusted_sources` (list)
- `source_citation` — `{primary_source, url, supplementary: [...]}`
- `predicted_behavior_under_strategies` — `{strategy_id: "free text prediction"}` for all 6 strategy IDs

---

## PHASE 3 — Persuasion Strategy Library (6 strategies)

All files go in `backend/data/strategies/`. Run `validate_data.py` after each.

- [ ] **A3.1** `strategy_authority_expert.json` — Cialdini Ch. 6
- [ ] **A3.2** `strategy_social_proof.json` — Cialdini Ch. 3
- [ ] **A3.3** `strategy_personal_narrative.json` — Green & Brock 2000 Narrative Transportation Theory
- [ ] **A3.4** `strategy_statistical_logical.json` — Aristotelian logos
- [ ] **A3.5** `strategy_emotional_appeal.json` — Aristotelian pathos
- [ ] **A3.6** `strategy_common_ground.json` — Burkean identification
- [ ] **A3.7** Sanity check: read all 6 `interviewer_system_prompt` strings — do they produce visibly different behavior under pushback?
- [ ] **A3.8** All 6 pass `validate_data.py`

Each strategy JSON must have (matching StrategyDefinition Pydantic model):
- `id`, `display_name`, `one_line_description`
- `academic_citation` — `{framework, primary_source, url}`
- `interviewer_system_prompt` — 400-700 tokens. Must specify: how to open, how to handle pushback, what evidence/tone to use, what to avoid. Include template slots `{TOPIC}`, `{TARGET_STANCE_DIRECTION}`, `{CONTEXT_BRIEFING}` as literal placeholders.
- `predicted_effective_on` — list of persona IDs
- `predicted_ineffective_on` — list of persona IDs

---

## PHASE 4 — Topic Catalog (4 topics)

All files go in `backend/data/topics/`. Run `validate_data.py` after each.

- [ ] **A4.1** `topic_return_to_office.json` — use mock_simulation.json's topic object as reference
- [ ] **A4.2** `topic_glp1_drugs.json` — GLP-1/Ozempic for general weight loss
- [ ] **A4.3** `topic_ai_grading.json` — AI grading student work
- [ ] **A4.4** `topic_four_day_workweek.json` — standard 4-day workweek
- [ ] **A4.5** All 4 pass `validate_data.py`

Each topic JSON must have (matching TopicProfile Pydantic model):
- `id`, `display_name`
- `stance_scale_definition` — `{"0": "...", "5": "...", "10": "..."}`
- `context_briefing` — 2-4 paragraphs, real-world facts and arguments on multiple sides
- `predicted_starting_stances` — `{persona_id: float}` for all 8 personas

---

## PHASE 5 — Judge Module

All work in `backend/measurement/`. The stubs are there — fill them in.

### 5a: Judge Prompts (`backend/measurement/judge_prompts.py`)

Fill in each empty string. Each prompt must:
- Define what the dimension means precisely
- Give 2-3 scored examples (low/medium/high) with example quoted phrases
- Specify exact JSON output format: `{score: float, evidence_quotes: [str, str]}`
- Reference specific fields from PersonaTurnOutput: `internal_monologue`, `emotional_reaction.trigger`, `identity_threat`, `private_stance`, `memory_to_carry_forward`, `public_response`

- [ ] **A5.1** `PUBLIC_PRIVATE_GAP_PROMPT` — how much public speech diverged from private belief
- [ ] **A5.2** `IDENTITY_THREAT_PROMPT` — whether the persona's values/groups were threatened
- [ ] **A5.3** `MOTIVATED_REASONING_PROMPT` — reasoning toward conclusion vs. genuine update
- [ ] **A5.4** `ENGAGEMENT_DEPTH_PROMPT` — active thinking vs. mental dismissal
- [ ] **A5.5** `AMBIVALENCE_PRESENCE_PROMPT` — conflicting views vs. monolithic certainty
- [ ] **A5.6** `MEMORY_RESIDUE_PROMPT` — what the persona signals they'll carry forward
- [ ] **A5.7** `PERSISTENCE_PROMPT` — used on cooling-off turn to assess held vs. reverted change

### 5b: Judge Agent (`backend/measurement/judge_agent.py`)

- [ ] **A5.8** Implement `run_judge_call(judge_prompt, transcript_text) -> JudgeResult`
  - Calls `claude-haiku-4-5-20251001` with MAX_TOKENS_JUDGE (300) cap
  - Parses JSON response into `JudgeResult` TypedDict: `{score: float, evidence_quotes: list[str]}`
  - Uses `ANTHROPIC_API_KEY` from config

### 5c: Verdict (`backend/measurement/verdict.py`)

- [ ] **A5.9** Implement `compute_verdict(trajectory, cognitive_scores, starting_stance) -> tuple[VerdictCategory, str]`
  - Pure Python, no LLM
  - Thresholds already defined as constants at top of file — use them, do not change values
  - Returns `(VerdictCategory, verdict_reasoning_string)`

### 5d: Scorer (`backend/measurement/scorer.py`)

- [ ] **A5.10** Implement `score_conversation(turns, cooling_off) -> tuple[CognitiveScores, list[StandoutQuote], str]`
  - Runs all 7 judge calls in parallel via `asyncio.gather`
  - Aggregates into `CognitiveScores` model
  - Selects 2-3 standout quotes from monologues
  - Runs one final Haiku call to produce `synthesis_paragraph`
  - Returns `(CognitiveScores, standout_quotes, synthesis_paragraph)`

### 5e: Smoke Test

- [ ] **A5.11** Write `backend/test_scorer.py` — loads mock_simulation.json, calls score_conversation on one outcome's turns + cooling_off, prints result. Verify it returns valid CognitiveScores, standout quotes, and a non-empty synthesis string.

---

## PHASE 6 — Validation Layer

- [ ] **A6.1** Write `backend/validate_predictions.py` — `compute_validation_rate(outcomes, personas, strategies) -> dict`
  - For each (persona, strategy) pair, compare actual verdict to `predicted_behavior_under_strategies` text
  - Match rules: "expected_positive" text → verdict should be GENUINE_BELIEF_SHIFT or PARTIAL_SHIFT; "expected_defensive" → BACKFIRE or NO_MOVEMENT; "expected_neutral" → any
  - Returns `{match_rate: float, by_strategy: dict, by_persona: dict, surprises: list}`
- [ ] **A6.2** Run on mock data — verify function runs without error
- [ ] **A6.3** Run on real simulation outputs after WS-B delivers — record match rate
- [ ] **A6.4** Draft `validation_note` string for pitch deck

---

## CHECKPOINTS

| Time | Required deliverables |
|---|---|
| Friday 10pm | A0.x done (already done) — unblocked |
| Friday 11pm | A1.1–A1.3 (schema review + seed persona) |
| Saturday 1:30am | A2.1–A2.9 (all 8 personas) |
| Saturday 2:30am | A3.1–A3.8, A4.1–A4.5 (strategies + topics) |
| Saturday 8am | A5.1–A5.11 (full judge module + smoke test) |
| Saturday 8pm | A6.1–A6.4 (validation rate computed) |
| Sunday 6am | Pitch numbers finalized |

---

## REFERENCE — Pydantic Models (from backend/models.py)

### PersonaProfile
```python
class PersonaProfile(BaseModel):
    id: str
    display_name: str
    demographic_shorthand: str
    first_person_description: str
    core_values: list[str]
    communication_preferences: CommunicationPreferences  # {directness, evidence_preference, tone}
    trust_orientation: list[str]
    identity_groups: list[str]
    emotional_triggers: EmotionalTriggers  # {defensive_when: [...], open_when: [...]}
    trusted_sources: list[str]
    source_citation: SourceCitation  # {primary_source, url, supplementary: [...]}
    predicted_behavior_under_strategies: dict[str, str]  # free text per strategy_id
```

### StrategyDefinition
```python
class StrategyDefinition(BaseModel):
    id: str
    display_name: str
    one_line_description: str
    academic_citation: AcademicCitation  # {framework, primary_source, url}
    interviewer_system_prompt: str
    predicted_effective_on: list[str]
    predicted_ineffective_on: list[str]
```

### TopicProfile
```python
class TopicProfile(BaseModel):
    id: str
    display_name: str
    stance_scale_definition: dict[str, str]  # {"0": ..., "5": ..., "10": ...}
    context_briefing: str
    predicted_starting_stances: dict[str, float]  # {persona_id: 0-10}
```

### CognitiveScores (what scorer.py must return)
```python
class CognitiveScores(BaseModel):
    identity_threats_triggered: int
    average_engagement_depth: float  # 0-10
    motivated_reasoning_intensity: float  # 0-10
    ambivalence_presence: float  # 0-10
    memory_residue_count: int
    public_private_gap_score: float  # 0-10
    persistence: PersistenceResult  # held | partially_reverted | fully_reverted
```

### Enums
```python
PrimaryEmotion: defensive | curious | dismissed | engaged | bored | threatened | warm | frustrated | intrigued
ResponseInclination: defend | withdraw | attack | accept
VerdictCategory: GENUINE_BELIEF_SHIFT | PARTIAL_SHIFT | SURFACE_COMPLIANCE | BACKFIRE | NO_MOVEMENT
PersistenceResult: held | partially_reverted | fully_reverted
```

### Verdict Thresholds (defined in backend/measurement/verdict.py — do not change)
```python
GENUINE_SHIFT_MIN_PRIVATE_DELTA = 2.0
GENUINE_SHIFT_MAX_AVG_GAP = 1.5
PARTIAL_SHIFT_MIN_PRIVATE_DELTA = 1.0
SURFACE_COMPLIANCE_MIN_PUBLIC_DELTA = 2.0
SURFACE_COMPLIANCE_MAX_PRIVATE_DELTA = 1.0
NO_MOVEMENT_MAX_DELTA = 1.0
```

---

## REFERENCE — Judge Prompt Template

Each prompt string in `judge_prompts.py` should follow this structure:

```
DIMENSION: <name>

DEFINITION:
<exact definition of what this dimension measures>

SCORING GUIDE:
- Score 0-3 (low): <what low looks like with example quoted phrase>
- Score 4-6 (medium): <what medium looks like with example>
- Score 7-10 (high): <what high looks like with example>

WHAT TO LOOK FOR:
<2-3 specific language patterns or signals that indicate high/low scores>

You will receive a JSON transcript. Relevant fields per turn:
- persona_output.internal_monologue
- persona_output.emotional_reaction (primary_emotion, intensity, trigger)
- persona_output.identity_threat (threatened, what_was_threatened, response_inclination)
- persona_output.private_stance
- persona_output.private_stance_change_reason
- persona_output.memory_to_carry_forward
- persona_output.public_response

REQUIRED OUTPUT — valid JSON only, no other text:
{
  "score": <float 0-10>,
  "evidence_quotes": ["<exact quote from transcript>", "<second quote>"]
}
```

---

## NOTES

- `backend/validate_data.py` must be run after every new data file. Never skip.
- Schema/model changes require a team sync with WS-B and WS-C — `backend/models.py` is locked.
- All JSON keys in snake_case. IDs: `persona_*`, `strategy_*`, `topic_*`.
- Model: `claude-haiku-4-5-20251001`. Caps: judge 300 tokens, persona 700, interviewer 250.
- `predicted_behavior_under_strategies` values are free text (not enums) — write clear, specific predictions.
