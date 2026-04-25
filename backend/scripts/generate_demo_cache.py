"""
Step 12 — Generate demo cache.

Runs run_simulation() for every persona × topic pair and writes results to
output/simulations/<scenario_id>.json.

Usage:
  # Dry-run: 1 persona × 1 topic × 3 turns to estimate cost
  python3 scripts/generate_demo_cache.py --dry-run

  # Full run: all 8 personas × 4 topics × 6 turns
  python3 scripts/generate_demo_cache.py

Options:
  --dry-run     Run 1 persona × 1 topic × 3 turns for cost estimation only
  --turns N     Override number of turns (default: from config.DEFAULT_TURNS)
  --persona ID  Run only this persona (can repeat)
  --topic ID    Run only this topic (can repeat)
"""
import argparse
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_TURNS, OUTPUT_DIR
from data.loader import list_all
from simulation.pipeline import run_simulation


async def run_one(
    scenario_id: str,
    persona_id: str,
    topic_id: str,
    num_turns: int,
) -> dict:
    t0 = time.monotonic()
    try:
        await run_simulation(scenario_id, persona_id, topic_id, num_turns)
        elapsed = time.monotonic() - t0
        out_path = OUTPUT_DIR / f"{scenario_id}.json"
        size_kb = out_path.stat().st_size / 1024 if out_path.exists() else 0
        return {"scenario_id": scenario_id, "status": "ok", "elapsed": elapsed, "size_kb": size_kb}
    except Exception as exc:
        elapsed = time.monotonic() - t0
        return {"scenario_id": scenario_id, "status": "error", "elapsed": elapsed, "error": str(exc)}


async def main(args: argparse.Namespace) -> None:
    all_personas = list_all("personas")
    all_topics = list_all("topics")

    personas = args.persona if args.persona else all_personas
    topics = args.topic if args.topic else all_topics
    num_turns = args.turns

    if args.dry_run:
        personas = [all_personas[0]]
        topics = [all_topics[0]]
        num_turns = 3
        print(f"DRY RUN: {personas[0]} × {topics[0]} × {num_turns} turns\n")
    else:
        print(f"Full run: {len(personas)} personas × {len(topics)} topics × {num_turns} turns")
        print(f"Total scenarios: {len(personas) * len(topics)}\n")

    pairs = [
        (f"{p}__{t}", p, t)
        for p in personas
        for t in topics
    ]

    results = []
    total = len(pairs)
    for i, (scenario_id, persona_id, topic_id) in enumerate(pairs, 1):
        print(f"[{i}/{total}] {scenario_id} ...", end=" ", flush=True)
        result = await run_one(scenario_id, persona_id, topic_id, num_turns)
        results.append(result)
        if result["status"] == "ok":
            print(f"done in {result['elapsed']:.1f}s  ({result['size_kb']:.1f} KB)")
        else:
            print(f"FAILED in {result['elapsed']:.1f}s — {result['error'][:80]}")

    # Summary
    ok = [r for r in results if r["status"] == "ok"]
    failed = [r for r in results if r["status"] == "error"]
    total_time = sum(r["elapsed"] for r in results)

    print(f"\n{'=' * 60}")
    print(f"Done: {len(ok)}/{total} scenarios succeeded in {total_time:.1f}s total")
    if failed:
        print(f"FAILED ({len(failed)}):")
        for r in failed:
            print(f"  {r['scenario_id']}: {r['error'][:100]}")
    if ok:
        avg_time = sum(r["elapsed"] for r in ok) / len(ok)
        print(f"Average time per scenario: {avg_time:.1f}s")
        files = [OUTPUT_DIR / f"{r['scenario_id']}.json" for r in ok]
        print(f"Output dir: {OUTPUT_DIR}")
        print(f"Files written: {len(files)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Lumos demo cache")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run 1 persona × 1 topic × 3 turns for cost estimation")
    parser.add_argument("--turns", type=int, default=DEFAULT_TURNS,
                        help=f"Number of turns per conversation (default: {DEFAULT_TURNS})")
    parser.add_argument("--persona", action="append", metavar="ID",
                        help="Run only this persona (can repeat)")
    parser.add_argument("--topic", action="append", metavar="ID",
                        help="Run only this topic (can repeat)")
    args = parser.parse_args()
    asyncio.run(main(args))
