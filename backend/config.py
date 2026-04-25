"""
SHARED — Runtime settings consumed by any backend module.

All tunable constants live here so they can be adjusted in one place.
Reads ANTHROPIC_API_KEY from environment. Everything else has a sane default.
No business logic — only constants and environment reads.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL_ID: str = "claude-haiku-4-5-20251001"

# ---------------------------------------------------------------------------
# Token caps per call type (enforced at each agent call site)
# ---------------------------------------------------------------------------

MAX_TOKENS_PERSONA: int = 1024
MAX_TOKENS_INTERVIEWER: int = 250
MAX_TOKENS_JUDGE: int = 300

# ---------------------------------------------------------------------------
# Conversation settings
# ---------------------------------------------------------------------------

DEFAULT_TURNS: int = 6

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
PERSONAS_DIR = DATA_DIR / "personas"
STRATEGIES_DIR = DATA_DIR / "strategies"
TOPICS_DIR = DATA_DIR / "topics"

OUTPUT_DIR = BASE_DIR / "output" / "simulations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
