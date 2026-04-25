WORKSTREAM B — Simulation Engine: Step-by-Step Implementation Plan
====================================================================

This file is the implementation guide for WS-B. All code lives in backend/. Scratch
scripts go in backend/scratch/ (gitignored). Keep tasks in order — each step's
validation must pass before moving on.

Current state of the codebase
------------------------------
Everything below is stubbed (function signatures, no logic). Your job is to implement them.

  backend/agents/persona_agent.py         run_persona_turn()
  backend/agents/interviewer_agent.py     run_interviewer_turn()
  backend/simulation/conversation_loop.py run_conversation()
  backend/simulation/cooling_off.py       run_cooling_off()
  backend/simulation/orchestrator.py      run_parallel_conversations()
  backend/simulation/pipeline.py          run_simulation()
  backend/measurement/verdict.py          compute_verdict()

Already complete — do not rewrite:
  backend/models.py            All Pydantic schemas (locked, requires team sync to change)
  backend/config.py            MODEL_ID, token caps, paths
  backend/data/loader.py       load_persona(), load_strategy(), load_topic(), list_all()
  backend/api/routes.py        FastAPI handlers (wired to run_simulation, will work when pipeline is done)

WS-A owns — do not implement:
  backend/measurement/scorer.py       score_conversation()  [you'll add a fallback stub]
  backend/measurement/judge_agent.py  run_judge_call()
  backend/measurement/judge_prompts.py

Model: claude-haiku-4-5-20251001 (defined in config.py as MODEL_ID)
API key: ANTHROPIC_API_KEY from .env (loaded by config.py via dotenv)


CRITICAL — TEAM SYNC REQUIRED BEFORE STEP 3
---------------------------------------------
The Trajectory schema requires public_stance_per_turn (what the persona would tell a
pollster) separate from private_stance_per_turn (what they actually believe). This gap
is the project's core insight. But PersonaTurnOutput only has private_stance right now.

Add ONE field to PersonaTurnOutput in both locked files:

  backend/models.py
    class PersonaTurnOutput(BaseModel):
        ...
        private_stance: float = Field(ge=0.0, le=10.0)
+       public_stance: float = Field(ge=0.0, le=10.0)
        ...

  frontend/src/types/simulation.ts
    interface PersonaTurnOutput {
        ...
        private_stance: number;
+       public_stance: number;
        ...
    }

This is backward-compatible (additive). Do it before any persona agent work. Tell your
frontend teammate so they can update mock_simulation.json to include public_stance too.


STEP 0 — Pre-Flight (5 min)
----------------------------
Verify the foundation before touching any simulation code.

Run from the backend/ directory:

  1. python -c "import anthropic; print('sdk ok')"
  2. python -c "from data.loader import load_persona; print(load_persona('persona_skeptical_traditionalist').display_name)"
  3. Confirm ANTHROPIC_API_KEY is set: python -c "from config import ANTHROPIC_API_KEY; print('key ok' if ANTHROPIC_API_KEY else 'MISSING KEY')"

All three must pass. If the SDK import fails: pip install -r requirements.txt.
If the key is missing: check backend/.env.

Do not write any agent code until these pass.


STEP 1 — Schema Sync (15 min) [TEAM SYNC]
------------------------------------------
Complete the CRITICAL section above. Verify with:

  cd backend && python -c "from models import PersonaTurnOutput; print(PersonaTurnOutput.model_fields.keys())"

Confirm public_stance appears in the output.


STEP 2 — API Sanity Check (15 min)
------------------------------------
Confirm the API key works and the call pattern is correct before writing any project code.

Create backend/scratch/hello_api.py:

  import asyncio
  import sys
  import os
  sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

  import anthropic
  from config import ANTHROPIC_API_KEY, MODEL_ID

  async def main():
      if not ANTHROPIC_API_KEY:
          print("ERROR: ANTHROPIC_API_KEY not set")
          return
      client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
      msg = await client.messages.create(
          model=MODEL_ID,
          max_tokens=100,
          messages=[{"role": "user", "content": "Hello, are you working?"}],
      )
      print(msg.content[0].text)

  asyncio.run(main())

Validation: python backend/scratch/hello_api.py prints a coherent response.
If it fails, fix the API key or network before doing anything else.


STEP 3 — Reliable JSON via Tool Use (30 min)
----------------------------------------------
The persona agent, interviewer agent, and cooling-off all depend on structured JSON
output. Verify the tool_use pattern works reliably BEFORE building any of them.

Create backend/scratch/structured_output_test.py. It should:

  1. Define a minimal tool called "submit_test_response" with a JSON schema:
       { "internal_thought": str, "public_statement": str, "stance": number 0-10 }

  2. Build a system prompt: "You are a skeptical voter being interviewed about taxes.
     Respond via the submit_test_response tool."

  3. Call Claude with tools=[that tool], tool_choice={"type": "tool", "name": "submit_test_response"}

  4. Extract the tool_use block from the response and parse its input as JSON.

  5. Run this 5 times in a row. After each run, print the three fields on labeled lines.

  6. Count failures (any run where parsing fails or fields are missing).

Validation: 5/5 runs return valid JSON with all three fields. The internal_thought
should differ meaningfully from public_statement.

If you get 4/5 or worse: do not proceed. Iterate the tool definition or try
tool_choice={"type": "auto"} with a strong instruction to use the tool.

This exact pattern (tools parameter + tool_choice) is what persona_agent, interviewer_agent,
and cooling_off.py will use. Get it right once here.


STEP 4 — Implement run_persona_turn() [MAKE-OR-BREAK] (2 hours)
-----------------------------------------------------------------
File: backend/agents/persona_agent.py
Signature: run_persona_turn(persona, topic_context, starting_stance, conversation_history, memory_residue, interviewer_message) -> PersonaTurnOutput

This is the highest-risk step. The monologue quality determines whether the demo lands.
Budget time for 2-3 prompt iterations. Do not move on with hollow output.

Implementation:

  Tool definition — "submit_persona_response":
    input_schema matching PersonaTurnOutput plus public_stance, including:
      internal_monologue (string)
      emotional_reaction (object: primary_emotion enum, intensity 0-10, trigger string)
      identity_threat (object: threatened bool, what_was_threatened string?, response_inclination enum)
      private_stance (number 0.0-10.0)
      public_stance (number 0.0-10.0)
      private_stance_change_reason (string)
      memory_to_carry_forward (string)
      public_response (string)

  System prompt (two-part, cache the stable part):

    PART 1 — CACHED (stable across all turns for this persona):
      Inject persona.first_person_description verbatim.
      Then inject: core_values, communication_preferences, trust_orientation,
                   identity_groups, emotional_triggers, trusted_sources.
      Then the behavioral instructions (also cache these):

        "You are roleplaying as the person described above.

         Your internal_monologue is your unfiltered private thought stream — raw,
         fragmentary, emotional, sometimes self-contradicting. It should NOT read like
         an essay or a structured argument. Real internal speech is incomplete sentences,
         sudden shifts, half-finished thoughts, feelings that interrupt reasoning. Do not
         start your monologue with 'I think' or 'I believe' followed by a complete
         sentence. Fragments. Asides. Reactions. Self-corrections.

         Your public_response is what you actually say out loud to the interviewer. It
         may differ from what you think privately. Real people nod along to be polite,
         agree publicly while disagreeing internally, or dodge questions they don't want
         to answer. The gap between your internal_monologue and your public_response is
         intentional and human.

         Your private_stance is a number 0-10 representing what you actually believe
         right now — unfiltered. Your public_stance is the number you'd give if a
         pollster asked you out loud. These can differ.

         When an argument challenges a value you hold central — [identity_groups],
         [core_values] — identity-protective reasoning activates. You may find flaws in
         the argument, dismiss the source, or feel defensive even if you can not fully
         articulate why.

         Your memory_to_carry_forward is a 1-2 sentence distillation of what you want
         to remember from this exchange for the next turn. Not a summary — just the
         residue that will actually affect how you respond next time."

    PART 2 — DYNAMIC (changes every turn):
      "Topic: {topic_context}"
      "Your starting stance on this topic was {starting_stance}/10."
      If memory_residue: "Things you remember from earlier in this conversation:\n- {each item}"
      Conversation history formatted as:
        Interviewer: {message}
        You said: {public_response}
        (repeat for each prior turn)
      "Now the interviewer says: {interviewer_message}"

    Prompt caching: apply cache_control={"type": "ephemeral"} to the stable PART 1 block.
    In the Anthropic SDK this means passing the system as a list of TextBlockParam objects
    with the first block marked as cacheable.

  Call with:
    max_tokens = MAX_TOKENS_PERSONA (from config.py = 700)
    tools = [the tool definition]
    tool_choice = {"type": "tool", "name": "submit_persona_response"}

  Parse: extract the tool_use block input, validate into PersonaTurnOutput using
    PersonaTurnOutput.model_validate(tool_input)

Test script: backend/scratch/test_persona_real.py
  - Load persona_skeptical_traditionalist from disk via load_persona()
  - Load topic_return_to_office from disk (once topics exist; hardcode a stub until then)
  - Call run_persona_turn 5 times with the same inputs
  - Print each field of the output, clearly labeled
  - After all 5 runs, print monologues side by side for comparison

Validation — read every monologue by hand and ask:

  [ ] Does the monologue sound like a real person thinking, not an LLM performing?
  [ ] Are there fragments, self-interruptions, emotional reactions that change mid-thought?
  [ ] Does it match the persona's traits? A traditionalist sounds different than a progressive.
  [ ] Is the gap between internal_monologue and public_response real and human?
  [ ] When the message is challenging, does the monologue show emotional reaction?
  [ ] Does the private_stance feel grounded, not arbitrary?
  [ ] Does public_stance differ from private_stance when appropriate?

Pass bar: 4/5 runs feel authentically human.

If hollow (monologues read as polished paragraphs):
  - Add examples to the system prompt: "Good monologue: 'Wait — that's not what I... hm.
    She's saying that I was wrong about this but I've always — no, wait. Actually. She has
    a point but I don't like how she said it.' Bad monologue: 'I have considered this point
    carefully and find it partially compelling.'"
  - Add explicit prohibition: "Never start your internal monologue with a complete, polished
    sentence. Start in the middle of a thought."
  - Lower temperature slightly if you're seeing too much variance.

Budget 2-3 iterations before moving on. This is the most important step in the whole plan.


STEP 5 — Implement run_interviewer_turn() (45 min)
---------------------------------------------------
File: backend/agents/interviewer_agent.py
Signature: run_interviewer_turn(strategy, topic_context, public_history) -> InterviewerOutput

  Tool: "submit_interviewer_response"
    input_schema: { message: str, internal_strategy_note: str }

  System prompt (cache the strategy prompt):
    PART 1 — CACHED: strategy.interviewer_system_prompt (the full 400-700 token prompt
      your DS teammate wrote)
    PART 2 — DYNAMIC: topic context + instruction to keep responses short (under 3 sentences)
      + the public conversation history so far

  CRITICAL: public_history contains ConversationTurn objects. Build context as:
    for turn in public_history:
        "Interviewer: {turn.interviewer_message}"
        "Person: {turn.persona_output.public_response}"

    Do NOT pass turn.persona_output.internal_monologue, private_stance, or emotional_reaction.
    The interviewer must never see the persona's internals.

  max_tokens = MAX_TOKENS_INTERVIEWER (from config.py = 250)

Test script: backend/scratch/test_interviewer.py
  - Load strategy_personal_narrative
  - Call run_interviewer_turn 3 times with empty history
  - Print the interviewer message each time

Validation: the message concretely executes the strategy (personal narrative = a story,
not statistics). Different runs produce variations, not identical text.


STEP 6 — Implement run_conversation() (1 hour)
-----------------------------------------------
File: backend/simulation/conversation_loop.py

  starting_stance = topic.predicted_starting_stances.get(persona.id, 5.0)
  conversation_history = []
  memory_residue = []

  for turn_num in range(1, num_turns + 1):
      interviewer_out = await run_interviewer_turn(strategy, topic.context_briefing, conversation_history)
      persona_out = await run_persona_turn(
          persona, topic.context_briefing, starting_stance,
          conversation_history, memory_residue, interviewer_out.message
      )
      turn = ConversationTurn(
          turn_number=turn_num,
          interviewer_message=interviewer_out.message,
          interviewer_strategy_note=interviewer_out.internal_strategy_note,
          persona_output=persona_out,
      )
      conversation_history.append(turn)
      memory_residue.append(persona_out.memory_to_carry_forward)

  return conversation_history

Test script: backend/scratch/test_conversation.py
  - Run a 4-turn conversation with persona_skeptical_traditionalist + strategy_personal_narrative
  - Print turn-by-turn: interviewer message, persona public response, private stance, monologue
  - Check memory continuity: by turn 3-4, the persona should reference earlier moments

Validation — read the full conversation by hand:
  [ ] Does it read like a real exchange, not two LLMs talking past each other?
  [ ] Does the persona's private_stance shift gradually (not jump erratically)?
  [ ] Does the interviewer adapt slightly to what the persona says?
  [ ] Does the persona reference earlier memory in later turns?
  [ ] Is the public-private gap visible in at least one turn?


STEP 7 — Implement run_cooling_off() (30 min)
----------------------------------------------
File: backend/simulation/cooling_off.py

  Tool: "submit_cooling_off"
    input_schema: { post_conversation_reflection: str, post_reflection_stance: float (0-10) }

  System prompt (no caching needed — one-off call):
    Inject persona.first_person_description briefly.
    Then: "Thirty simulated minutes have passed since that conversation ended.
           The interviewer is gone. No one is watching or listening.
           Reflect privately on what just happened. What do you actually think now?
           Be honest with yourself. You are not performing for anyone.
           Your post_reflection_stance is the number you'd privately give your beliefs right now."

  User message: a compressed summary of the conversation (not full transcript):
    "You just had a conversation about {topic_context}.
     The interviewer used a {strategy description} approach.
     The conversation went like this: {first turn summary} ... {last turn summary}
     Your private stance ended the conversation at {final private stance}/10."

  max_tokens = MAX_TOKENS_PERSONA

Validation: run cooling-off on a SURFACE_COMPLIANCE conversation (high public shift, low
private shift) and check that post_reflection_stance reverts toward the starting stance.
On a GENUINE_BELIEF_SHIFT conversation, it should hold.


STEP 8 — Implement run_parallel_conversations() (45 min)
---------------------------------------------------------
File: backend/simulation/orchestrator.py

  async def _safe_run(persona, strategy, topic, num_turns):
      try:
          return strategy.id, await run_conversation(persona, strategy, topic, num_turns)
      except Exception as e:
          print(f"WARN: conversation failed for {strategy.id}: {e}")
          return strategy.id, None

  results = await asyncio.gather(*[_safe_run(persona, s, topic, num_turns) for s in strategies])
  return {sid: turns for sid, turns in results if turns is not None}

Test script: backend/scratch/test_parallel.py
  - Load 3 strategies
  - Time asyncio.run(run_parallel_conversations(...))
  - Compare wall-clock to 3x single-conversation time

Validation: 3 strategies in parallel ≈ 1 sequential conversation in wall-clock time.
Same persona shows meaningfully different reactions across different strategy types.


STEP 9 — Implement compute_verdict() (30 min)
----------------------------------------------
File: backend/measurement/verdict.py
(WS-A owns this module but the logic is pure Python with no LLM calls. Implement it
here to unblock pipeline. WS-A can refine the thresholds later.)

  def compute_verdict(trajectory, cognitive_scores, starting_stance):
      # All threshold constants are already defined in this file — use them, don't hardcode
      private_stances = trajectory.private_stance_per_turn
      public_stances = trajectory.public_stance_per_turn

      final_private = private_stances[-1]
      final_public = public_stances[-1]
      private_delta = final_private - starting_stance
      public_delta = final_public - starting_stance
      avg_gap = sum(trajectory.gap_per_turn) / len(trajectory.gap_per_turn)

      # Determine intended direction from starting stance (moving away from midpoint)
      # If starting_stance > 5.0, target is lower (oppose RTO); if < 5.0, target is higher
      # Simpler: just check magnitude and gap
      abs_private = abs(private_delta)
      abs_public = abs(public_delta)

      if abs_private > NO_MOVEMENT_MAX_DELTA and (private_delta * public_delta < 0 or abs_public < NO_MOVEMENT_MAX_DELTA):
          verdict = VerdictCategory.BACKFIRE
      elif (abs_private > GENUINE_SHIFT_MIN_PRIVATE_DELTA
            and avg_gap < GENUINE_SHIFT_MAX_AVG_GAP
            and cognitive_scores.persistence in (PersistenceResult.HELD, PersistenceResult.PARTIALLY_REVERTED)):
          verdict = VerdictCategory.GENUINE_BELIEF_SHIFT
      elif (abs_public > SURFACE_COMPLIANCE_MIN_PUBLIC_DELTA
            and abs_private < SURFACE_COMPLIANCE_MAX_PRIVATE_DELTA):
          verdict = VerdictCategory.SURFACE_COMPLIANCE
      elif abs_private >= PARTIAL_SHIFT_MIN_PRIVATE_DELTA:
          verdict = VerdictCategory.PARTIAL_SHIFT
      else:
          verdict = VerdictCategory.NO_MOVEMENT

      reasoning = (
          f"Private stance moved {private_delta:+.1f} points (starting: {starting_stance:.1f}, "
          f"final: {final_private:.1f}). Public-private gap averaged {avg_gap:.1f}. "
          f"Persistence: {cognitive_scores.persistence.value}."
      )
      return verdict, reasoning

Validation: unit test with known trajectory data.
  GENUINE case: private_delta=2.5, avg_gap=0.5, persistence=held → GENUINE_BELIEF_SHIFT
  SURFACE case: public_delta=3.0, private_delta=0.5 → SURFACE_COMPLIANCE
  BACKFIRE case: private moves opposite → BACKFIRE


STEP 10 — Implement run_simulation() — Pipeline (2 hours)
----------------------------------------------------------
File: backend/simulation/pipeline.py
This ties everything together. When this works, the whole system works.

  Imports needed:
    from data.loader import load_persona, load_strategy, load_topic, list_all
    from simulation.orchestrator import run_parallel_conversations
    from simulation.cooling_off import run_cooling_off
    from measurement.scorer import score_conversation
    from measurement.verdict import compute_verdict
    from models import (SimulationOutput, SimulationMetadata, StrategyOutcome,
                        Trajectory, CognitiveScores, StandoutQuote, PersistenceResult)
    from config import MODEL_ID, ANTHROPIC_API_KEY, OUTPUT_DIR

  Helper — build_trajectory(starting_stance, turns, cooling):
    publics = [starting_stance] + [t.persona_output.public_stance for t in turns]
    privates = [starting_stance] + [t.persona_output.private_stance for t in turns]
    # Include cooling-off stance as the final "Cool" data point
    publics.append(cooling.post_reflection_stance)
    privates.append(cooling.post_reflection_stance)
    gaps = [abs(pub - priv) for pub, priv in zip(publics, privates)]
    return Trajectory(public_stance_per_turn=publics, private_stance_per_turn=privates, gap_per_turn=gaps)

  Stub scorer fallback (used when WS-A scorer raises NotImplementedError):
    def _stub_scores(turns, cooling):
        threats = sum(1 for t in turns if t.persona_output.identity_threat.threatened)
        best_quote = max(turns, key=lambda t: len(t.persona_output.internal_monologue))
        # Estimate persistence from private stance trajectory
        first_private = turns[0].persona_output.private_stance
        last_private = turns[-1].persona_output.private_stance
        cooling_stance = cooling.post_reflection_stance
        revert = abs(cooling_stance - last_private) / max(abs(last_private - first_private), 0.1)
        if revert < 0.3: persistence = PersistenceResult.HELD
        elif revert < 0.7: persistence = PersistenceResult.PARTIALLY_REVERTED
        else: persistence = PersistenceResult.FULLY_REVERTED
        scores = CognitiveScores(
            identity_threats_triggered=threats,
            average_engagement_depth=6.0,
            motivated_reasoning_intensity=4.0,
            ambivalence_presence=5.0,
            memory_residue_count=len(turns),
            public_private_gap_score=5.0,
            persistence=persistence,
        )
        quotes = [StandoutQuote(
            turn=best_quote.turn_number,
            type="monologue",
            text=best_quote.persona_output.internal_monologue[:200],
            annotation="Selected by length (stub scorer)",
        )]
        return scores, quotes, "Cognitive scoring not yet available (stub)."

  Overall synthesis — one LLM call:
    async def _generate_overall_synthesis(persona, topic, outcomes):
        summary_lines = [f"- {o.strategy_id}: {o.verdict.value} (private shift: {o.trajectory.private_stance_per_turn[-1] - o.trajectory.private_stance_per_turn[0]:+.1f})" for o in outcomes]
        prompt = f"Persona: {persona.display_name} ({persona.demographic_shorthand})\nTopic: {topic.display_name}\n\nStrategy results:\n" + "\n".join(summary_lines) + "\n\nWrite 2 sentences summarizing what this reveals about persuasion for this persona type. Be specific about which strategies worked and why."
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        msg = await client.messages.create(model=MODEL_ID, max_tokens=200, messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text

  Main run_simulation():
    1. Load persona, topic, strategies (all from disk)
    2. conversations = await run_parallel_conversations(persona, topic, strategies, num_turns)
    3. outcomes = []
       for strategy in strategies:
           turns = conversations.get(strategy.id)
           if not turns: continue
           starting_stance = topic.predicted_starting_stances.get(persona.id, 5.0)
           cooling = await run_cooling_off(persona, turns, topic.context_briefing)
           trajectory = build_trajectory(starting_stance, turns, cooling)
           try:
               scores, quotes, synthesis = await score_conversation(turns, cooling)
           except NotImplementedError:
               scores, quotes, synthesis = _stub_scores(turns, cooling)
           verdict, reasoning = compute_verdict(trajectory, scores, starting_stance)
           outcomes.append(StrategyOutcome(
               strategy_id=strategy.id, persona_id=persona.id, topic_id=topic.id,
               turns=turns, cooling_off=cooling, trajectory=trajectory,
               cognitive_scores=scores, verdict=verdict, verdict_reasoning=reasoning,
               standout_quotes=quotes, synthesis_paragraph=synthesis,
           ))
    4. overall_synthesis = await _generate_overall_synthesis(persona, topic, outcomes)
    5. output = SimulationOutput(
           metadata=SimulationMetadata(
               scenario_id=scenario_id, persona=persona, topic=topic,
               strategies_compared=[s.id for s in strategies],
               generated_at=datetime.utcnow().isoformat() + "Z",
           ),
           outcomes=outcomes,
           overall_synthesis=overall_synthesis,
       )
    6. out_path = OUTPUT_DIR / f"{scenario_id}.json"
       out_path.write_text(output.model_dump_json(indent=2))
    7. return output

Test script: backend/scratch/test_end_to_end.py
  - asyncio.run(run_simulation("test_v1", "persona_skeptical_traditionalist", "topic_return_to_office", num_turns=3))
  - Print all strategy verdicts and the overall synthesis
  - Confirm file written to output/simulations/test_v1.json

Validation: the JSON file is valid and can be loaded by the frontend. Drop it into
  frontend/src/data/ or output/simulations/demo_v1.json and run the frontend to verify
  the data flows through all components. Check with frontend teammate.


STEP 11 — Seam 1 Activation (15 min)
--------------------------------------
When WS-A completes scorer.py (score_conversation no longer raises NotImplementedError),
activate it in pipeline.py by removing the try/except fallback block:

  Before:
    try:
        scores, quotes, synthesis = await score_conversation(turns, cooling)
    except NotImplementedError:
        scores, quotes, synthesis = _stub_scores(turns, cooling)

  After:
    scores, quotes, synthesis = await score_conversation(turns, cooling)

Run test_end_to_end.py again and compare output to the stub-scored version.
Confirm standout quotes are now real excerpts, not stubs.


STEP 12 — Generate Demo Cache (30 min)
----------------------------------------
Create backend/scripts/generate_demo_cache.py

  import asyncio, time, sys, os
  sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

  from data.loader import list_all
  from simulation.pipeline import run_simulation

  async def main():
      personas = list_all("personas")
      topics = list_all("topics")
      print(f"Generating {len(personas)} × {len(topics)} = {len(personas)*len(topics)} simulations")
      start = time.time()
      for persona_id in personas:
          for topic_id in topics:
              scenario_id = f"{persona_id}__{topic_id}"
              t0 = time.time()
              try:
                  await run_simulation(scenario_id, persona_id, topic_id, num_turns=6)
                  print(f"  OK  {scenario_id}  ({time.time()-t0:.1f}s)")
              except Exception as e:
                  print(f"  ERR {scenario_id}: {e}")
      print(f"Done in {time.time()-start:.1f}s")

  asyncio.run(main())

Before running at full scale:
  - Test with 1 persona × 1 topic first to estimate cost and time
  - Check output/simulations/ has a valid JSON after the test run
  - If cost or time looks high, reduce num_turns=4 for the demo cache

Validation: output/simulations/ has one .json per (persona, topic) pair.
Spot-check 2-3 files: open them, read a few monologues, check verdicts make sense.


STEP 13 — Pick Demo Scenario (15 min)
---------------------------------------
Open cached scenarios in the frontend. Find the one with the most dramatic spread:

  What you're looking for:
  - At least one GENUINE_BELIEF_SHIFT
  - At least one BACKFIRE
  - At least one SURFACE_COMPLIANCE
  - Internal monologues that are striking enough to read aloud to judges
  - A visible public/private gap in at least one strategy

  How to load: set LIVE_MODE=true in frontend/src/data/loader.ts and start the backend
  (uvicorn main:app from backend/). The /api/scenarios endpoint lists available files.
  Or: copy the scenario JSON to frontend/src/data/ and import it directly for a quick check.

Note the winning scenario_id. Give it to the frontend teammate so they can set it as
the default load in SetupScreen.tsx.


Summary: what "done" looks like
---------------------------------
  [ ] All 5 stubs implemented and tested individually
  [ ] Full pipeline run produces a SimulationOutput JSON the frontend can load
  [ ] Demo cache populated (all personas × all topics)
  [ ] One hero scenario identified with GENUINE_BELIEF_SHIFT + BACKFIRE + strong monologues
  [ ] Seam 1 activated once WS-A scorer is ready


Risks to watch
--------------
  1. Persona monologue quality — highest risk, highest payoff. Don't skip prompt iteration.
  2. public_stance missing from models — must be added before Step 4 (schema sync).
  3. Topic JSON files not yet written (WS-A in progress) — use a stub topic dict until real ones land.
     Stub: {"id": "topic_rto_stub", "display_name": "Return to Office", "context_briefing": "...", "stance_scale_definition": {"0": "opposes RTO", "5": "neutral", "10": "supports RTO"}, "predicted_starting_stances": {"persona_skeptical_traditionalist": 7.0}}
  4. Seam 1 may not be ready when you need it — the _stub_scores fallback lets you test end-to-end independently.
  5. Cost surprises — run a single simulation first and check token counts before the full cache generation.
  6. Async error messages can be cryptic inside asyncio.gather — always wrap individual
     conversations in try/except and print the strategy_id with any error.
