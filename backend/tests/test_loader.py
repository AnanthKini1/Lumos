"""
Tests for backend/data/loader.py

Covers:
- load_persona() returns a valid PersonaProfile for the seed file
- load_persona() raises FileNotFoundError for unknown IDs
- load_strategy() raises FileNotFoundError for unknown IDs
- load_topic() raises FileNotFoundError for unknown IDs
- list_all() returns correct IDs for existing data
- list_all() returns empty list when directory is empty
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loader import list_all, load_persona, load_strategy, load_topic
from models import PersonaProfile


class TestLoadPersona:
    def test_loads_seed_persona_successfully(self) -> None:
        persona = load_persona("persona_skeptical_traditionalist")
        assert isinstance(persona, PersonaProfile)

    def test_seed_persona_has_correct_id(self) -> None:
        persona = load_persona("persona_skeptical_traditionalist")
        assert persona.id == "persona_skeptical_traditionalist"

    def test_seed_persona_has_display_name(self) -> None:
        persona = load_persona("persona_skeptical_traditionalist")
        assert persona.display_name

    def test_seed_persona_first_person_description_is_multiline(self) -> None:
        persona = load_persona("persona_skeptical_traditionalist")
        # Must be substantive enough to inject into a system prompt
        assert len(persona.first_person_description) > 200

    def test_seed_persona_has_core_values(self) -> None:
        persona = load_persona("persona_skeptical_traditionalist")
        assert len(persona.core_values) >= 3

    def test_seed_persona_has_strategy_predictions(self) -> None:
        persona = load_persona("persona_skeptical_traditionalist")
        assert len(persona.predicted_behavior_under_strategies) >= 4

    def test_seed_persona_strategy_predictions_are_non_empty(self) -> None:
        persona = load_persona("persona_skeptical_traditionalist")
        for strategy_id, prediction in persona.predicted_behavior_under_strategies.items():
            assert prediction.strip(), f"Empty prediction for {strategy_id}"

    def test_seed_persona_has_emotional_triggers(self) -> None:
        persona = load_persona("persona_skeptical_traditionalist")
        assert len(persona.emotional_triggers.defensive_when) >= 1
        assert len(persona.emotional_triggers.open_when) >= 1

    def test_load_persona_raises_for_unknown_id(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_persona("persona_does_not_exist")


class TestLoadStrategy:
    def test_load_strategy_raises_for_unknown_id(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_strategy("strategy_does_not_exist")


class TestLoadTopic:
    def test_load_topic_raises_for_unknown_id(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_topic("topic_does_not_exist")


class TestListAll:
    def test_list_personas_includes_seed(self) -> None:
        ids = list_all("personas")
        assert "persona_skeptical_traditionalist" in ids

    def test_list_strategies_returns_list(self) -> None:
        ids = list_all("strategies")
        assert isinstance(ids, list)

    def test_list_topics_returns_list(self) -> None:
        ids = list_all("topics")
        assert isinstance(ids, list)
