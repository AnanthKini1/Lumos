"""
Step 2 — API sanity check.
Confirms the API key loads and the model responds before any project logic runs.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config import ANTHROPIC_API_KEY, MODEL_ID


async def main() -> None:
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set. Check .env or environment.")
        sys.exit(1)

    print(f"Model: {MODEL_ID}")
    print(f"Key prefix: {ANTHROPIC_API_KEY[:8]}...")
    print("Calling API...")

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    msg = await client.messages.create(
        model=MODEL_ID,
        max_tokens=64,
        messages=[{"role": "user", "content": "Hello — respond with exactly: API_OK"}],
    )

    reply = msg.content[0].text.strip()
    print(f"Response: {reply}")

    if "API_OK" in reply:
        print("PASS: API key works and model is responding.")
    else:
        print("WARN: model responded but not with the expected token. Check manually.")


if __name__ == "__main__":
    asyncio.run(main())
