"""
WS-A — Conversation scorer. This is the entry point for Seam 1.

Exposes score_conversation() — the single function that WS-B's pipeline.py
calls after conversations complete. WS-B imports nothing else from measurement/.

Internally, this module:
  - Calls judge_agent.run_judge_call() once per cognitive dimension (parallelized)
  - Aggregates individual dimension scores into a CognitiveScores record
  - Selects 2-3 standout quotes from the monologues
  - Generates a synthesis paragraph via one final summarizer LLM call
  - Returns (CognitiveScores, list[StandoutQuote], synthesis_paragraph)

WS-B's pipeline does not know how scoring works. It calls score_conversation()
and gets back a result. That function signature is the entire contract.
"""

from models import CognitiveScores, ConversationTurn, CoolingOff, StandoutQuote


async def score_conversation(
    turns: list[ConversationTurn],
    cooling_off: CoolingOff,
) -> tuple[CognitiveScores, list[StandoutQuote], str]:
    """
    Score a completed conversation across all cognitive dimensions.

    Returns:
        (CognitiveScores, standout_quotes, synthesis_paragraph)
    """
    raise NotImplementedError
