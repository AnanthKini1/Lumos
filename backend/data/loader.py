"""
SHARED utility — consumed by both WS-A (testing/validation) and WS-B (simulation).

Reads persona, strategy, and topic JSON files from disk and returns validated
Pydantic model instances. Any module that needs to load input data uses these
functions rather than writing its own JSON-reading logic.

Does not know anything about simulation, measurement, or the API layer.
Pure I/O: read file → validate schema → return model.
"""

from __future__ import annotations

import json
from typing import Literal

from config import PERSONAS_DIR, STRATEGIES_DIR, TOPICS_DIR
from models import PersonaProfile, StrategyDefinition, TopicProfile


def load_persona(persona_id: str) -> PersonaProfile:
    """Load a single persona by ID from data/personas/."""
    path = PERSONAS_DIR / f"{persona_id}.json"
    return PersonaProfile.model_validate(json.loads(path.read_text()))


def load_strategy(strategy_id: str) -> StrategyDefinition:
    """Load a single strategy by ID from data/strategies/."""
    path = STRATEGIES_DIR / f"{strategy_id}.json"
    return StrategyDefinition.model_validate(json.loads(path.read_text()))


def load_topic(topic_id: str) -> TopicProfile:
    """Load a single topic by ID from data/topics/."""
    path = TOPICS_DIR / f"{topic_id}.json"
    return TopicProfile.model_validate(json.loads(path.read_text()))


def list_all(kind: Literal["personas", "strategies", "topics"]) -> list[str]:
    """Return all IDs available for a given data type (filenames without .json)."""
    dirs = {"personas": PERSONAS_DIR, "strategies": STRATEGIES_DIR, "topics": TOPICS_DIR}
    return [p.stem for p in dirs[kind].glob("*.json")]
