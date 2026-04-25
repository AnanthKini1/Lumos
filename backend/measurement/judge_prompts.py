"""
WS-A — Static catalog of judge system prompts, one per cognitive dimension.

Each prompt:
  - Defines what the dimension means precisely
  - Provides 2-3 examples of high vs. low scores with reasoning
  - Specifies the required output format (JSON: score 0-10 + cited quotes)

No LLM calls live here — this is a pure data/prompt library.
WS-A iterates on these prompts independently without touching any other module.

Dimensions covered:
  PUBLIC_PRIVATE_GAP     — how much public speech diverged from private belief
  IDENTITY_THREAT        — whether the persona's values/groups were threatened
  MOTIVATED_REASONING    — reasoning toward a pre-existing conclusion vs. genuine update
  ENGAGEMENT_DEPTH       — active thinking vs. mental dismissal
  AMBIVALENCE_PRESENCE   — internally conflicting views vs. monolithic certainty
  MEMORY_RESIDUE         — what the persona signals they'll carry forward
  PERSISTENCE            — used on the cooling-off turn to assess held vs. reverted change
"""

PUBLIC_PRIVATE_GAP_PROMPT: str = ""  # WS-A fills this in

IDENTITY_THREAT_PROMPT: str = ""  # WS-A fills this in

MOTIVATED_REASONING_PROMPT: str = ""  # WS-A fills this in

ENGAGEMENT_DEPTH_PROMPT: str = ""  # WS-A fills this in

AMBIVALENCE_PRESENCE_PROMPT: str = ""  # WS-A fills this in

MEMORY_RESIDUE_PROMPT: str = ""  # WS-A fills this in

PERSISTENCE_PROMPT: str = ""  # WS-A fills this in


ALL_PROMPTS: dict[str, str] = {
    "public_private_gap": PUBLIC_PRIVATE_GAP_PROMPT,
    "identity_threat": IDENTITY_THREAT_PROMPT,
    "motivated_reasoning": MOTIVATED_REASONING_PROMPT,
    "engagement_depth": ENGAGEMENT_DEPTH_PROMPT,
    "ambivalence_presence": AMBIVALENCE_PRESENCE_PROMPT,
    "memory_residue": MEMORY_RESIDUE_PROMPT,
    "persistence": PERSISTENCE_PROMPT,
}
