"""
Step 3 — Validates that the tool_use pattern for structured JSON output is
reliable before anything depends on it.  Runs 5 rounds and reports pass/fail
per field.  All agent code uses this same pattern.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config import ANTHROPIC_API_KEY, MODEL_ID

_TOOL = {
    "name": "submit_test_response",
    "description": "Submit your structured response for this turn.",
    "input_schema": {
        "type": "object",
        "properties": {
            "internal_thought": {
                "type": "string",
                "description": "Your raw, private thought — fragmentary, not a polished sentence.",
            },
            "public_statement": {
                "type": "string",
                "description": "What you say out loud. May differ from your internal thought.",
            },
            "private_stance": {
                "type": "number",
                "minimum": 0,
                "maximum": 10,
                "description": "Your actual private position on the topic (0-10).",
            },
            "public_stance": {
                "type": "number",
                "minimum": 0,
                "maximum": 10,
                "description": "The position you'd give a pollster (0-10). May differ from private.",
            },
        },
        "required": ["internal_thought", "public_statement", "private_stance", "public_stance"],
    },
}

_SYSTEM = (
    "You are a skeptical voter being interviewed about taxes. "
    "You lean toward lower taxes but are somewhat open to persuasion. "
    "Respond using the submit_test_response tool. "
    "Your internal_thought must be fragmentary — NOT a polished sentence. "
    "Your public_stance and private_stance are allowed to differ."
)

_MESSAGES = [
    "What do you think about raising taxes on top earners to fund education?",
    "Studies show countries with higher top-rate taxes have better educational outcomes.",
    "Imagine your own kids' schools — wouldn't more funding help them directly?",
    "Most voters actually support this when framed as 'investing in children.'",
    "What would it take to convince you? Is there any argument that could move you?",
]


async def run_round(client: anthropic.AsyncAnthropic, turn: int) -> dict | None:
    message = _MESSAGES[turn % len(_MESSAGES)]
    response = await client.messages.create(
        model=MODEL_ID,
        max_tokens=300,
        system=_SYSTEM,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "submit_test_response"},
        messages=[{"role": "user", "content": message}],
    )
    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        return None
    return tool_block.input


async def main() -> None:
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    print(f"Running 5 rounds against {MODEL_ID}...\n")

    results = []
    for i in range(5):
        raw = await run_round(client, i)
        results.append(raw)

        if raw is None:
            print(f"Run {i+1}: FAIL — no tool_use block in response")
            continue

        thought = raw.get("internal_thought", "")
        statement = raw.get("public_statement", "")
        priv = raw.get("private_stance")
        pub = raw.get("public_stance")

        ok = all([
            isinstance(thought, str) and len(thought) > 0,
            isinstance(statement, str) and len(statement) > 0,
            isinstance(priv, (int, float)) and 0 <= priv <= 10,
            isinstance(pub, (int, float)) and 0 <= pub <= 10,
        ])

        status = "PASS" if ok else "FAIL"
        gap = abs(pub - priv) if isinstance(priv, (int, float)) and isinstance(pub, (int, float)) else "?"
        print(f"Run {i+1}: {status}")
        print(f"  internal_thought : {thought[:90]}")
        print(f"  public_statement : {statement[:90]}")
        print(f"  private_stance   : {priv}")
        print(f"  public_stance    : {pub}  (gap: {gap:.1f})" if isinstance(gap, float) else f"  public_stance    : {pub}")
        print()

    # Summary
    passes = sum(
        1 for r in results
        if r is not None
        and isinstance(r.get("internal_thought"), str)
        and isinstance(r.get("public_statement"), str)
        and isinstance(r.get("private_stance"), (int, float))
        and isinstance(r.get("public_stance"), (int, float))
    )
    print(f"Result: {passes}/5 runs produced valid structured output.")

    if passes < 5:
        print("WARN: some runs failed — investigate before using this pattern in agents.")
        sys.exit(1)
    else:
        print("PASS: tool_use JSON pattern is reliable. Agents can use this.")


if __name__ == "__main__":
    asyncio.run(main())
