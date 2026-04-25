"""
Step 6 — End-to-end pipeline test.

Runs run_simulation() with 2 strategies and 3 turns to verify the full pipeline:
  - parallel conversations
  - cooling-off reflection
  - scoring + verdict
  - JSON output written to disk

Expected verdicts:
  - personal_narrative: GENUINE_BELIEF_SHIFT or PARTIAL_SHIFT (Karen responds to stories)
  - authority_expert: BACKFIRE or NO_MOVEMENT (Karen distrusts credentials)
"""
import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch list_all to only run 2 strategies for this test
from data import loader as _loader

_ORIGINAL_LIST_ALL = _loader.list_all


def _two_strategies(kind: str) -> list[str]:
    if kind == "strategies":
        return ["strategy_personal_narrative", "strategy_authority_expert"]
    return _ORIGINAL_LIST_ALL(kind)


_loader.list_all = _two_strategies

from simulation.pipeline import run_simulation  # noqa: E402 — import after patch
from config import OUTPUT_DIR  # noqa: E402


async def main() -> None:
    scenario_id = "test_step6_v1"
    print(f"Running pipeline: {scenario_id}")
    print("  persona: persona_skeptical_traditionalist")
    print("  topic:   topic_return_to_office")
    print("  strategies: personal_narrative + authority_expert")
    print("  turns: 3\n")

    t0 = time.monotonic()
    output = await run_simulation(
        scenario_id=scenario_id,
        persona_id="persona_skeptical_traditionalist",
        topic_id="topic_return_to_office",
        num_turns=3,
    )
    elapsed = time.monotonic() - t0

    print(f"Completed in {elapsed:.1f}s\n")
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    for outcome in output.outcomes:
        traj = outcome.trajectory
        delta = traj.private_stance_per_turn[-1] - traj.private_stance_per_turn[0]
        print(f"\nStrategy: {outcome.strategy_id}")
        print(f"  Verdict      : {outcome.verdict.value}")
        print(f"  Reasoning    : {outcome.verdict_reasoning}")
        print(f"  Trajectory   : {[f'{v:.1f}' for v in traj.private_stance_per_turn]}")
        print(f"  Private delta: {delta:+.1f}")
        if outcome.cooling_off:
            print(f"  Cooling-off  : {outcome.cooling_off.post_reflection_stance:.1f} "
                  f"— {outcome.cooling_off.post_conversation_reflection[:120]}")
        print(f"  Synthesis    : {outcome.synthesis_paragraph}")

    print(f"\nOverall synthesis:\n  {output.overall_synthesis}")

    # Verify JSON on disk
    out_path = OUTPUT_DIR / f"{scenario_id}.json"
    assert out_path.exists(), f"Output file not found: {out_path}"
    with open(out_path) as f:
        parsed = json.load(f)
    assert parsed["metadata"]["scenario_id"] == scenario_id
    print(f"\nJSON written and parseable: {out_path}")
    print(f"  strategies: {parsed['metadata']['strategies_compared']}")
    print(f"  outcomes  : {len(parsed['outcomes'])}")


if __name__ == "__main__":
    asyncio.run(main())
