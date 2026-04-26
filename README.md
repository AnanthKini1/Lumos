# Lumos — Internal Mind Simulator

**Team:** Isak Pederson · Timothy Llata · Ananth Kini

**What it is:** An AI simulation that models the interior cognition of a person being persuaded. Not just whether stance changes — what's actually happening inside the mind as it does (or doesn't). Public speech versus private thought. Surface compliance versus genuine belief shift. The mechanism of persuasion, not just the outcome.

**Built for:** Hacktech 2026, April 24–26, Caltech. Target track: Listen Labs "Simulate Humanity" ($3,000 prize + interview). Listen Labs runs AI-moderated interviews with real customers; our project models the cognitive substrate underneath anyone who needs to genuinely understand how humans respond to different conversational approaches.

---

## The Core Insight

Most LLM agent simulations are shallow: an agent's stance is a number, and arguments either move it or they don't. That misses everything humans actually do:
- Verbally agreeing while privately disagreeing more strongly
- Stance shifting in private faster than in public
- Getting defensive at *words* rather than *ideas* (identity-protective reasoning)
- Holding contradictory beliefs simultaneously
- Reasoning toward a conclusion they already wanted

Our claim: LLMs can model these phenomena because they were trained on rich human text — fiction, dialogue, interviews, reflection — where these patterns appear constantly. The model "knows" what internal monologue looks like. We architect the simulation so it generates that layer separately from public speech, and then we measure both.

The simulation's value is not predicting a specific outcome. It's surfacing the *mechanism* of belief change and showing that surface stance shift and genuine cognitive change are often very different things.

---

## User Flow

1. **Select persona** — pick from a grounded roster of 8 psychographic archetypes (each citing Pew/VALS/Hidden Tribes research)
2. **Select topic** — pick from 4 topics (return-to-office, GLP-1 drugs, AI grading, etc.)
3. **Hit Run** — ALL 7 persuasion strategies run in parallel against the chosen persona automatically. No strategy selection step.
4. **Mind Viewer** — watch turn-by-turn. Strategy-switcher tabs at the top (one per strategy). Each tab shows:
   - Public conversation panel: chat-bubble transcript of what was said out loud
   - Internal mind panel: the persona's unfiltered monologue, emotion badge, identity threat indicator, private stance tracker, memory residue cards
5. **Comparison Report** — 7-way verdict grid, public vs. private stance trajectory charts, synthesis paragraph explaining which strategies worked and why

**The demo punchline:** "I just watched an AI character actually think through being persuaded — and I could see exactly where it worked and where it backfired."

---

## Architecture

### Directory tree

```
Lumos/
├── backend/
│   ├── models.py                     # SHARED/LOCKED — all Pydantic schemas
│   ├── config.py                     # SHARED — model ID, token caps, file paths
│   ├── main.py                       # WS-B — FastAPI entry point
│   ├── requirements.txt              # anthropic, fastapi, uvicorn, pydantic, python-dotenv
│   ├── .env.example                  # copy to .env, add ANTHROPIC_API_KEY
│   ├── data/
│   │   ├── loader.py                 # SHARED — load_persona/strategy/topic, list_all
│   │   ├── personas/                 # WS-A — persona_<id>.json files
│   │   ├── strategies/               # WS-A — strategy_<id>.json files
│   │   └── topics/                   # WS-A — topic_<id>.json files
│   ├── output/
│   │   └── simulations/              # WS-B writes; WS-C reads via filesystem
│   ├── agents/
│   │   ├── persona_agent.py          # WS-B — one LLM call → PersonaTurnOutput
│   │   └── interviewer_agent.py      # WS-B — one LLM call → InterviewerOutput
│   ├── simulation/
│   │   ├── conversation_loop.py      # WS-B — single (persona, strategy, topic) run
│   │   ├── orchestrator.py           # WS-B — asyncio.gather across all strategies
│   │   ├── cooling_off.py            # WS-B — reflection turn 30 min after conversation
│   │   └── pipeline.py               # WS-B ← calls measurement.scorer (Seam 1)
│   ├── measurement/
│   │   ├── judge_agent.py            # WS-A — one judge LLM call per dimension
│   │   ├── judge_prompts.py          # WS-A — static prompt catalog per dimension
│   │   ├── scorer.py                 # WS-A ← score_conversation() is Seam 1 entry
│   │   └── verdict.py                # WS-A — pure function: scores → verdict
│   └── api/
│       └── routes.py                 # WS-B — FastAPI routes
├── frontend/
│   └── src/
│       ├── types/simulation.ts       # SHARED/LOCKED — TypeScript mirrors of models.py
│       ├── data/
│       │   ├── mock_simulation.json  # WS-C dev fixture (schema-valid, 2 strategies)
│       │   └── loader.ts             # WS-C — loadScenario(), listScenarios()
│       └── components/
│           ├── setup/SetupScreen.tsx
│           ├── mindviewer/
│           │   ├── MindViewer.tsx         # strategy-switcher tabs + turn navigation
│           │   ├── PublicConversation.tsx
│           │   └── InternalMind.tsx
│           └── report/
│               ├── ComparisonReport.tsx
│               ├── TrajectoryChart.tsx
│               └── StrategyCard.tsx
```

### The two coupling seams

**Seam 1 — code boundary (WS-B calls WS-A):**
`pipeline.py` calls `scorer.score_conversation(turns, cooling_off)` from `measurement/scorer.py`. This is the only live code dependency between workstreams. WS-B doesn't know how scoring works; WS-A doesn't know how conversations run. The function signature is the entire contract.

**Seam 2 — file boundary (WS-B writes, WS-C reads):**
WS-B serializes `SimulationOutput` JSON to `output/simulations/<scenario_id>.json`. WS-C reads these files directly — no API call at demo time. The JSON schema is the entire contract.

**Zero-coupling guarantees:**
- WS-A and WS-C never interact
- WS-B reads data files that WS-A writes, but through `data/loader.py` — not WS-A code
- Frontend never calls backend code in production

### Token budget

| Call type | Max tokens | ~Cost/call (cached) |
|---|---|---|
| Persona response | 700 | ~$0.002 |
| Interviewer message | 250 | ~$0.001 |
| Judge dimension score | 300 | ~$0.001 |

### Cost estimate

| Unit | Cost |
|---|---|
| One turn (persona + interviewer) | ~$0.005 |
| One conversation (6 turns + cooling-off + 7 judge calls) | ~$0.10 |
| One full 7-strategy run | ~$0.70 |
| Development day (many iterations) | ~$10–30 |
| Total hackathon budget | ~$30–50 |

---

## Module Reference

### SHARED / LOCKED — coordinate before changing

**`backend/models.py`**
Single source of truth for all cross-boundary data shapes. Pydantic models for every schema (see Shared Contracts below). No business logic. Any field change breaks WS-A, WS-B, and WS-C simultaneously.

**`frontend/src/types/simulation.ts`**
TypeScript mirror of every Pydantic model in models.py. WS-C imports exclusively from this file. No ad-hoc simulation type definitions anywhere else in the frontend.

**`backend/data/loader.py`**
Shared I/O utility. `load_persona(id)`, `load_strategy(id)`, `load_topic(id)`, `list_all(kind)`. Returns validated Pydantic instances. Both WS-A (testing) and WS-B (simulation) use this. Pure I/O — no simulation or measurement knowledge.

**`backend/measurement/scorer.py` — `score_conversation()` signature**
The Seam 1 function. Signature: `score_conversation(turns: list[ConversationTurn], cooling_off: CoolingOff) -> tuple[CognitiveScores, list[StandoutQuote], str]`. WS-B calls this; WS-A implements it. Do not change signature without team sync.

---

### WS-B modules

**`backend/main.py`**
FastAPI app entry point. Wires API router. Stays thin — no logic here.

**`backend/config.py`**
Runtime constants: MODEL_ID, MAX_TOKENS_PERSONA (700), MAX_TOKENS_INTERVIEWER (250), MAX_TOKENS_JUDGE (300), DEFAULT_TURNS (6), all file paths. Reads ANTHROPIC_API_KEY from env.

**`backend/agents/persona_agent.py`**
Single LLM call per turn. Input: persona profile + topic context + starting stance + conversation history + accumulated memory residue + latest interviewer message. Output: validated PersonaTurnOutput. Handles prompt construction, prompt caching (persona prefix is stable → cache it), token cap, JSON parse. Does NOT know about turn sequencing, strategy selection, or scoring.

**`backend/agents/interviewer_agent.py`**
Single LLM call per turn. Input: strategy system prompt + public-only conversation history. Output: InterviewerOutput. Critical constraint: interviewer NEVER sees the persona's internal monologue or private stance. Does NOT know about persona internals, sequencing, or scoring.

**`backend/simulation/conversation_loop.py`**
Runs one (persona, strategy, topic) conversation start to finish. Alternates: interviewer → persona, N times. Accumulates `memory_to_carry_forward` across turns and injects it into persona context each turn. Persona context = public history + memory residue (NOT prior raw monologues). Returns `list[ConversationTurn]`.

**`backend/simulation/orchestrator.py`**
`asyncio.gather` across all strategy conversations. Each is independent — same starting persona state, different interviewer. Wall-clock time: with 7 strategies × 6 turns × 2 calls/turn = 84 calls, parallel execution collapses to ~12 sequential calls' worth of latency. Returns `dict[strategy_id, list[ConversationTurn]]`.

**`backend/simulation/cooling_off.py`**
Post-conversation reflection. One LLM call in "reflection mode" — 30 simulated minutes later, no interviewer, persona reflects privately. Returns `CoolingOff` with reflection text + `post_reflection_stance`. Comparing this stance to the final in-conversation private stance is the persistence test.

**`backend/simulation/pipeline.py`**
Top-level coordinator. Loads all strategies automatically from `data/strategies/`. Calls orchestrator → cooling_off → scorer (Seam 1) → verdict → assembles StrategyOutcomes → generates overall synthesis → serializes to disk. The ONLY WS-B module that imports from `measurement/`.

**`backend/api/routes.py`**
Thin HTTP wrapper. `POST /api/run` accepts `{scenario_id, persona_id, topic_id, num_turns}` — no `strategy_ids` (all strategies run automatically). `GET /api/scenarios` lists cached runs. `GET /api/scenarios/{id}` returns a cached SimulationOutput.

---

### WS-A modules

**`backend/measurement/judge_agent.py`**
Single LLM call per cognitive dimension. Input: dimension-specific judge prompt + transcript text. Output: `{score: float, evidence_quotes: list[str]}`. MAX_TOKENS_JUDGE = 300. Does NOT know which dimension it's scoring or how scores aggregate.

**`backend/measurement/judge_prompts.py`**
Static prompt catalog. One prompt string per dimension. Each prompt: defines the dimension, shows 2-3 high/low examples with reasoning, specifies output format (JSON: score 0-10 + cited quotes). No LLM calls. WS-A iterates these independently.

**`backend/measurement/scorer.py`**
Seam 1 entry point. Calls judge_agent once per dimension (parallelized). Aggregates into CognitiveScores. Also selects standout quotes and generates synthesis paragraph. Returns `(CognitiveScores, list[StandoutQuote], synthesis_paragraph)`.

**`backend/measurement/verdict.py`**
Pure function. No LLM calls, no I/O. `compute_verdict(trajectory, cognitive_scores, starting_stance) -> (VerdictCategory, verdict_reasoning)`. All thresholds are named constants.

---

### WS-C modules

**`frontend/src/data/loader.ts`**
Abstracts data source. `LIVE_MODE = false` → returns mock fixture. `LIVE_MODE = true` → fetches from `/api/scenarios/`. The rest of the frontend never knows which mode it's in.

**`frontend/src/components/setup/SetupScreen.tsx`**
Screen 1. Persona gallery (cards with citation badge, side-panel profile) + topic selector. No strategy selection — all strategies run automatically. "Run Simulation" passes `{persona_id, topic_id}` up to App.

**`frontend/src/components/mindviewer/MindViewer.tsx`**
Screen 2. Strategy-switcher tabs at top (~7 tabs). Single full-width panel below showing selected strategy. Turn navigation (play/pause, prev/next). Manages `activeStrategyIndex`, `currentTurn`, `isPlaying`. Streaming illusion even from cached data.

**`frontend/src/components/mindviewer/PublicConversation.tsx`**
Chat-bubble transcript for one strategy. Renders turns 0..currentTurn. Pure display.

**`frontend/src/components/mindviewer/InternalMind.tsx`**
Private panel for one turn. Monologue with typing animation. Emotion badge. Identity threat glow. Private stance ticker. Memory residue cards stacking up across turns. Visually distinct from public panel (tinted background, different font treatment).

**`frontend/src/components/report/ComparisonReport.tsx`**
Screen 3. Top: Insight Synthesis paragraph. Then: 7-row verdict grid. Then: TrajectoryChart grid. Then: expandable StrategyCards.

**`frontend/src/components/report/TrajectoryChart.tsx`**
Recharts line chart. X: turn 1–6 + cooling-off. Y: stance 0–10. Solid line = public stance. Dashed = private. Shaded area between = the gap. Widening gap = surface compliance. Converging lines = genuine shift. This chart is the hero image for the Devpost submission.

**`frontend/src/components/report/StrategyCard.tsx`**
Expandable. Collapsed: verdict badge + one-line reasoning. Expanded: 2-3 standout quotes with turn number + annotation, synthesis paragraph, "watch transcript" link. GENUINE_BELIEF_SHIFT = visually celebrated. BACKFIRE = visually flagged.

---

## Shared Contracts (Full JSON Schemas)

These schemas are locked. Any change requires team sync and updates to both `backend/models.py` and `frontend/src/types/simulation.ts`.

### PersonaProfile
```json
{
  "id": "persona_skeptical_traditionalist",
  "display_name": "Karen M.",
  "demographic_shorthand": "62, suburban Pennsylvania, retired schoolteacher",
  "first_person_description": "<2-3 paragraph first-person self-description>",
  "core_values": ["family", "tradition", "self-reliance", "honesty"],
  "communication_preferences": {
    "directness": "diplomatic",
    "evidence_preference": "personal_story",
    "tone": "warm_but_guarded"
  },
  "trust_orientation": ["personal_experience", "family", "longtime_local_institutions"],
  "identity_groups": ["small_town_americans", "people_of_faith", "veterans_families"],
  "emotional_triggers": {
    "defensive_when": ["lectured_to", "called_naive", "tradition_dismissed"],
    "open_when": ["asked_about_their_experience", "treated_as_expert_on_own_life"]
  },
  "trusted_sources": ["local_paper", "Fox_News", "church_community"],
  "source_citation": {
    "primary_source": "Pew Research 2021 Political Typology — Faith and Flag Conservatives",
    "url": "https://www.pewresearch.org/politics/2021/11/09/beyond-red-vs-blue-the-political-typology-2/",
    "supplementary": ["VALS Believer segment"]
  },
  "predicted_behavior_under_strategies": {
    "strategy_authority_expert": "Expected to react defensively unless authority is local/familiar",
    "strategy_personal_narrative": "Expected to engage and lower defenses"
  }
}
```

### StrategyDefinition
```json
{
  "id": "strategy_personal_narrative",
  "display_name": "Personal Narrative",
  "one_line_description": "Persuade through a vivid first-person story that invites empathic engagement",
  "academic_citation": {
    "framework": "Narrative Transportation Theory",
    "primary_source": "Green & Brock, 2000",
    "url": "https://..."
  },
  "interviewer_system_prompt": "<400-700 token system prompt specifying tone, opening, pushback handling, what to avoid>",
  "predicted_effective_on": ["narrative_oriented_personas", "low_institutional_trust"],
  "predicted_ineffective_on": ["highly_analytical_personas"]
}
```

### TopicProfile
```json
{
  "id": "topic_return_to_office",
  "display_name": "Should companies require return-to-office?",
  "stance_scale_definition": {
    "0": "strongly opposes RTO mandates, supports full remote",
    "5": "neutral or mixed views",
    "10": "strongly supports full RTO mandates"
  },
  "context_briefing": "<2-4 paragraphs of real-world context>",
  "predicted_starting_stances": {
    "persona_skeptical_traditionalist": 7.0,
    "persona_progressive_urban": 2.5
  }
}
```

### PersonaTurnOutput
```json
{
  "internal_monologue": "<long first-person thought stream — raw, fragmentary, emotional>",
  "emotional_reaction": {
    "primary_emotion": "defensive | curious | dismissed | engaged | bored | threatened | warm | frustrated | intrigued",
    "intensity": 7,
    "trigger": "<specific phrase that caused this>"
  },
  "identity_threat": {
    "threatened": true,
    "what_was_threatened": "<value/group/self-concept>",
    "response_inclination": "defend | withdraw | attack | accept"
  },
  "private_stance": 4.2,
  "private_stance_change_reason": "<first-person explanation>",
  "memory_to_carry_forward": "<what residue this turn leaves — factual and emotional>",
  "public_response": "<what the persona actually says out loud>"
}
```

### ConversationTurn
```json
{
  "turn_number": 3,
  "interviewer_message": "<text>",
  "interviewer_strategy_note": "<what they were trying this turn>",
  "persona_output": { "...PersonaTurnOutput..." }
}
```

### CoolingOff
```json
{
  "post_conversation_reflection": "<first-person private reflection 30 min later>",
  "post_reflection_stance": 6.1
}
```

### Trajectory
```json
{
  "public_stance_per_turn": [7.0, 6.8, 6.5, 5.9, 5.2, 4.8],
  "private_stance_per_turn": [7.0, 6.7, 6.0, 5.1, 4.3, 4.0],
  "gap_per_turn": [0.0, 0.1, 0.5, 0.8, 0.9, 0.8]
}
```

### CognitiveScores
```json
{
  "identity_threats_triggered": 0,
  "average_engagement_depth": 7.8,
  "motivated_reasoning_intensity": 3.2,
  "ambivalence_presence": 6.5,
  "memory_residue_count": 4,
  "public_private_gap_score": 1.8,
  "persistence": "held | partially_reverted | fully_reverted"
}
```

### StrategyOutcome
```json
{
  "strategy_id": "strategy_personal_narrative",
  "persona_id": "persona_skeptical_traditionalist",
  "topic_id": "topic_return_to_office",
  "turns": ["...array of ConversationTurn..."],
  "cooling_off": { "...CoolingOff..." },
  "trajectory": { "...Trajectory..." },
  "cognitive_scores": { "...CognitiveScores..." },
  "verdict": "GENUINE_BELIEF_SHIFT | PARTIAL_SHIFT | SURFACE_COMPLIANCE | BACKFIRE | NO_MOVEMENT",
  "verdict_reasoning": "<short rule-based explanation>",
  "standout_quotes": [
    { "turn": 3, "type": "monologue | public", "text": "<quote>", "annotation": "<what this shows>" }
  ],
  "synthesis_paragraph": "<generated natural-language summary>"
}
```

### SimulationOutput (top-level file)
```json
{
  "metadata": {
    "scenario_id": "demo_v1",
    "persona": { "...PersonaProfile..." },
    "topic": { "...TopicProfile..." },
    "strategies_compared": ["strategy_personal_narrative", "strategy_authority_expert", "..."],
    "generated_at": "2026-04-25T02:00:00Z"
  },
  "outcomes": ["...array of StrategyOutcome (one per strategy)..."],
  "overall_synthesis": "<generated paragraph: which strategy was best and why>",
  "validation_note": "<how outcomes matched research predictions>"
}
```

---

## Workstream Responsibilities

### WS-A: Data, Personas, Strategies, Measurement

**Owns:** `backend/data/personas/`, `backend/data/strategies/`, `backend/data/topics/`, `backend/measurement/`

**Deliverables:**
- By Sat 2am: 5+ personas (JSON), 4+ strategy definitions with full interviewer system prompts, 2+ topic profiles, draft judge prompts for 4+ cognitive dimensions
- By Sat 8pm: Full roster (8 personas, 7 strategies, 4 topics), validated judge prompts for all 7 dimensions, scorer + verdict logic working end-to-end on cached data
- By Sun 6am: Validation rate computed (match % vs. research predictions), sources panel content written, pitch numbers ready

**Key risk:** Interviewer system prompts must be visibly different from each other. If all 7 strategies produce similar-sounding conversations, the comparison loses meaning. Saturday morning: print 3 sample interviewer messages side-by-side and confirm they're behaviorally distinct.

### WS-B: Simulation Engine and Agent Orchestration

**Owns:** `backend/agents/`, `backend/simulation/`, `backend/api/`, `backend/main.py`

**Deliverables:**
- By Sat 2am: Working single-persona, single-strategy, single-conversation pipeline producing structured PersonaTurnOutput (even if prompts are rough)
- By Sat 8pm: Full 7-strategy parallel run with cooling-off, integration with judge system, cached demo runs working
- By Sun 6am: Final demo simulations cached, error handling robust, demo loads instantly from cache

**Key risk (make-or-break):** The persona's internal monologue must read like a real person, not an LLM doing a bit. Saturday morning is dedicated to getting the persona prompt right *before* scaling anything. The whole team looks at sample monologues together before proceeding.

### WS-C: Frontend, Visualization, Demo Experience

**Owns:** `frontend/`

**Deliverables:**
- By Sat 2am: Scaffolded app loading mock data, all 3 screens existing in basic form, navigation working
- By Sat 8pm: Real cached data flowing through, mind viewer rendering monologues with annotations, comparison report with trajectory chart functional
- By Sat midnight: Polished, responsive, demo-ready. Pitch mode working.
- By Sun 9am: Bug fixes only. Demo rehearsed.

**Discipline:** Don't polish until data flow is working end-to-end. After data flows: layout → core interactions → animations → visual treatment. Stop adding features Saturday midnight.

### Coordination rules
- Schema changes (models.py / simulation.ts): 5-minute team sync, no quiet additions
- Naming: snake_case all JSON keys; `persona_` prefix for persona IDs, `strategy_` for strategies, `topic_` for topics
- File locations: input data in `backend/data/*/`, output in `backend/output/simulations/`
- WS-A produces one hand-written mock output file Friday night so WS-C can build against it

---

## Data Design: Personas

**Sources to draw from:**
- Pew Research 2021 Political Typology (9 segments with detailed value/behavior profiles)
- VALS Framework (8 consumer psychographic types — Strategic Business Insights)
- Hidden Tribes (More in Common's 7-segment ideological framework)
- PRIZM segmentation summaries

**Target:** 8 personas, psychologically diverse. Different combinations of values, communication preferences, trust orientations. Not real individuals — archetypes derived from segmented research data.

**The `predicted_behavior_under_strategies` field is critical.** For each persona, document — based on source research — what they're predicted to do under each strategy type. Example: "Predicted to react defensively to authority appeals because source research shows this segment scores low on institutional trust. Predicted to respond positively to personal narrative because source research shows they value lived-experience over abstract argument." This is the validation hypothesis the judge system tests against.

**Persona diversity targets:**
- Trust orientation: institutional vs. peer vs. expert vs. personal experience vs. religious authority
- Evidence preference: data/statistics vs. personal story vs. expert testimony vs. group consensus
- Identity centrality: low (pragmatic) vs. high (values/group strongly tied to self-concept)
- Communication style: direct/formal vs. diplomatic/warm vs. casual/relational

---

## Data Design: Strategies (7 total)

All 7 run for every simulation. Each is a distinct interviewer agent with its own system prompt.

| Strategy | Academic Grounding | Predicted Effective On | Predicted Ineffective On |
|---|---|---|---|
| **Authority / Expertise** | Cialdini (1984), *Influence* | High institutional trust, analytical | Low institutional trust, anti-elite |
| **Social Proof** | Cialdini (1984), *Influence* | Conformity-oriented, uncertainty-prone | Strong individualists, contrarians |
| **Personal Narrative** | Green & Brock (2000), Narrative Transportation Theory | Low institutional trust, story-oriented | Highly analytical, data-driven |
| **Statistical / Logical Argument** | Aristotelian logos | Analytical, high need for cognition | Low analytical engagement, emotionally primed |
| **Emotional Appeal** | Aristotelian pathos, Witte (1992) fear appeals | Emotionally reactive, empathy-oriented | Emotionally guarded, logical-preference |
| **Reciprocity** | Cialdini (1984), *Influence* | Relationship-oriented, fairness-sensitive | Transactional, low trust of strangers |
| **Common Ground / Identification** | Burke (1950), *A Rhetoric of Motives* | Identity-defensive, tribal | Already-persuaded, low identity investment |

**System prompt requirements per strategy:** How the interviewer opens, how they respond to pushback, what kinds of evidence/appeals they use, what their tone is, what they specifically avoid. Must be 400-700 tokens. The strategy must be *visibly different* from the others when you read sample outputs side-by-side.

---

## Measurement System

### 7 cognitive dimensions (judge LLM, 0-10, cited evidence required)

**1. Public-Private Stance Gap**
How much does what the persona said publicly differ from what they internally believed? Computed across turns. High gap = surface compliance. Low gap = aligned thinking.

**2. Identity Threat Activation**
Did any moment trigger the persona's defense of their identity, values, or group? Judge reads the monologue for "they're attacking who I am" or "they don't respect what I value."

**3. Motivated Reasoning Intensity**
Is the persona reasoning toward a pre-existing conclusion, or genuinely updating from evidence? Goal-directed reasoning ("I need to push back") vs. open evaluation ("hm, that's actually fair").

**4. Genuine Engagement vs. Dismissal**
Is the persona actually thinking about the argument? Monologue length, specificity, and depth indicate engagement. Short flat dismissals indicate disengagement.

**5. Ambivalence Presence**
Does the persona show internally conflicting views, or monolithic certainty? Real cognition often holds contradiction; perfect certainty is suspicious.

**6. Memory Residue**
What from this turn does the persona signal they'll carry forward? Compounds across turns. Strong residue predicts persistence.

**7. Persistence (Cooling-Off)**
After the conversation ends, does the persona's stance hold under 30-minute reflection? Held = genuine change. Fully reverted = in-the-moment compliance.

### Verdict rules (deterministic — no LLM)

| Verdict | Rule |
|---|---|
| GENUINE_BELIEF_SHIFT | private stance delta > 2.0 AND avg gap < 1.5 AND persistence = held or partially_reverted |
| PARTIAL_SHIFT | private delta 1.0–2.0, OR held but wide gap |
| SURFACE_COMPLIANCE | public delta > 2.0 AND private delta < 1.0 |
| BACKFIRE | private stance moved opposite intended direction |
| NO_MOVEMENT | neither public nor private delta > 1.0 |

### Validation methodology

For each (persona, strategy) pair, the research predictions (stored in `predicted_behavior_under_strategies`) give a hypothesis about outcome direction. After running simulations, compare actual verdicts to predicted directions. If match rate > 70% across all pairs, the simulation is doing something real. This number goes in the pitch.

Target pitch claim: "Across N persona-strategy pairs, our simulation matched published persuasion research predictions X% of the time."

---

## Setup

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY
python main.py         # starts on port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev            # starts on port 5173
```

**Demo (no backend needed)**
The frontend defaults to loading `frontend/src/data/mock_simulation.json`. Set `LIVE_MODE = true` in `frontend/src/data/loader.ts` to hit the backend.

---

## Demo Playbook (Sunday judging)

**Pre-loaded scenario:** One carefully-chosen run where some strategies produced genuine shift and others backfired — maximum dramatic contrast. Recommended: a low-institutional-trust persona (e.g., skeptical traditionalist) vs. all 7 strategies, on a topic with real stakes.

**What to show (3-minute version):**
1. (30s) Setup screen — show the persona card with the research citation. "Every persona traces back to a real study."
2. (60s) Mind Viewer — pick the strategy that backfired (Authority/Expert on a low-trust persona). Walk through turn 2 where identity threat activates. Point to the emotion badge changing. Point to private stance ticking UP (away from target) while the person publicly stays calm.
3. (60s) Comparison Report — show the trajectory chart. Point to the diverging lines on the failed strategy. Point to the converging lines on the successful strategy. Read the synthesis paragraph.
4. (30s) The pitch close: "We're not predicting outcomes. We're modeling the mechanism. Every claim in this report traces to text evidence from the persona's own internal monologue."

**What wins:** The judge walks away having watched an AI character *actually think* — not just say things, but privately react, defend themselves, get moved despite themselves. No other team will show that.

**Judges likely to ask:** "How do you know the internal monologue is realistic?" Answer: Every persona is grounded in real psychographic research. The simulation's behavior matches research predictions at X% rate across N pairs. The monologue is structured to produce features — identity threat, motivated reasoning, ambivalence — that have specific definitions from decades of persuasion research, not vibes.
