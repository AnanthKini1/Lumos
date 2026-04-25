"""
Tests for topic JSON data integrity.

Parametrized — every topic file in backend/data/topics/ is automatically
picked up. A new topic file must pass all checks before being committed.

Covers:
- Schema validation via Pydantic
- Stance scale has exactly the keys 0, 5, 10 with non-empty descriptions
- Context briefing minimum length
- Predicted starting stances cover all 8 known personas
- All stance values are within 0-10
- Topic ID matches filename
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loader import list_all, load_topic

REQUIRED_STANCE_KEYS = {"0", "5", "10"}
MIN_CONTEXT_LENGTH = 300


def all_topic_ids() -> list[str]:
    return list_all("topics")


def all_persona_ids() -> list[str]:
    return list_all("personas")


@pytest.mark.parametrize("topic_id", all_topic_ids())
class TestTopicDataQuality:
    def test_id_matches_filename(self, topic_id: str) -> None:
        topic = load_topic(topic_id)
        assert topic.id == topic_id, (
            f"Topic id field '{topic.id}' does not match filename '{topic_id}'"
        )

    def test_display_name_is_non_empty(self, topic_id: str) -> None:
        topic = load_topic(topic_id)
        assert topic.display_name.strip(), f"{topic_id}: display_name must not be empty"

    def test_stance_scale_has_required_keys(self, topic_id: str) -> None:
        topic = load_topic(topic_id)
        actual_keys = set(topic.stance_scale_definition.keys())
        assert REQUIRED_STANCE_KEYS == actual_keys, (
            f"{topic_id}: stance_scale_definition must have exactly keys '0', '5', '10'. "
            f"Got: {actual_keys}"
        )

    def test_stance_scale_descriptions_are_non_empty(self, topic_id: str) -> None:
        topic = load_topic(topic_id)
        for key, desc in topic.stance_scale_definition.items():
            assert desc.strip(), (
                f"{topic_id}: stance_scale_definition['{key}'] must not be empty"
            )

    def test_context_briefing_minimum_length(self, topic_id: str) -> None:
        topic = load_topic(topic_id)
        assert len(topic.context_briefing) >= MIN_CONTEXT_LENGTH, (
            f"{topic_id}: context_briefing too short "
            f"(got {len(topic.context_briefing)} chars, need >= {MIN_CONTEXT_LENGTH})"
        )

    def test_predicted_stances_cover_all_personas(self, topic_id: str) -> None:
        topic = load_topic(topic_id)
        persona_ids = set(all_persona_ids())
        covered = set(topic.predicted_starting_stances.keys())
        missing = persona_ids - covered
        assert not missing, (
            f"{topic_id}: predicted_starting_stances missing personas: {missing}"
        )

    def test_all_stance_values_in_range(self, topic_id: str) -> None:
        topic = load_topic(topic_id)
        for persona_id, stance in topic.predicted_starting_stances.items():
            assert 0.0 <= stance <= 10.0, (
                f"{topic_id}: stance for {persona_id} is {stance}, must be 0-10"
            )
