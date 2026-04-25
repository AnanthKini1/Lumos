"""
Tests for persona JSON data integrity.

These are data-quality tests, not code tests. They enforce content standards
that Pydantic can't catch: minimum description length, all 6 strategy IDs
present, prediction text is specific enough to be useful, etc.

A new persona file must pass all these tests before being committed.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PERSONAS_DIR
from data.loader import list_all, load_persona

# All strategy IDs that must appear in every persona's predictions
REQUIRED_STRATEGY_IDS = {
    "strategy_authority_expert",
    "strategy_social_proof",
    "strategy_personal_narrative",
    "strategy_statistical_logical",
    "strategy_emotional_appeal",
    "strategy_common_ground",
}


def all_persona_ids() -> list[str]:
    return list_all("personas")


@pytest.mark.parametrize("persona_id", all_persona_ids())
class TestPersonaDataQuality:
    def test_first_person_description_minimum_length(self, persona_id: str) -> None:
        persona = load_persona(persona_id)
        assert len(persona.first_person_description) >= 400, (
            f"{persona_id}: first_person_description too short to inject into system prompt "
            f"(got {len(persona.first_person_description)} chars, need >= 400)"
        )

    def test_first_person_description_uses_first_person(self, persona_id: str) -> None:
        persona = load_persona(persona_id)
        text = persona.first_person_description.lower()
        assert "i " in text or "my " in text or "i've" in text, (
            f"{persona_id}: first_person_description must be written in first person"
        )

    def test_has_minimum_core_values(self, persona_id: str) -> None:
        persona = load_persona(persona_id)
        assert len(persona.core_values) >= 3, (
            f"{persona_id}: need at least 3 core_values, got {len(persona.core_values)}"
        )

    def test_has_all_six_strategy_predictions(self, persona_id: str) -> None:
        persona = load_persona(persona_id)
        actual = set(persona.predicted_behavior_under_strategies.keys())
        missing = REQUIRED_STRATEGY_IDS - actual
        assert not missing, (
            f"{persona_id}: missing strategy predictions for: {missing}"
        )

    def test_strategy_predictions_are_substantive(self, persona_id: str) -> None:
        persona = load_persona(persona_id)
        for strategy_id in REQUIRED_STRATEGY_IDS:
            prediction = persona.predicted_behavior_under_strategies.get(strategy_id, "")
            assert len(prediction) >= 30, (
                f"{persona_id}.predicted_behavior_under_strategies[{strategy_id}] "
                f"is too vague (got {len(prediction)} chars, need >= 30)"
            )

    def test_has_defensive_and_open_triggers(self, persona_id: str) -> None:
        persona = load_persona(persona_id)
        assert persona.emotional_triggers.defensive_when, (
            f"{persona_id}: defensive_when triggers must not be empty"
        )
        assert persona.emotional_triggers.open_when, (
            f"{persona_id}: open_when triggers must not be empty"
        )

    def test_has_source_citation(self, persona_id: str) -> None:
        persona = load_persona(persona_id)
        assert persona.source_citation.primary_source.strip(), (
            f"{persona_id}: source_citation.primary_source must not be empty"
        )

    def test_id_matches_filename(self, persona_id: str) -> None:
        persona = load_persona(persona_id)
        assert persona.id == persona_id, (
            f"Persona id field '{persona.id}' does not match filename '{persona_id}'"
        )
