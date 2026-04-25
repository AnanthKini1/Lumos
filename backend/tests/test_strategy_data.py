"""
Tests for strategy JSON data integrity.

Parametrized — every strategy file in backend/data/strategies/ is automatically
picked up. A new strategy file must pass all checks before being committed.

Covers:
- Schema validation via Pydantic (caught by validate_data.py, confirmed here)
- Interviewer system prompt minimum length and required template slots
- Academic citation completeness
- Predicted effective/ineffective lists reference valid persona IDs
- Strategy ID matches filename
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PERSONAS_DIR
from data.loader import list_all, load_strategy

REQUIRED_TEMPLATE_SLOTS = ["{TOPIC}", "{TARGET_STANCE_DIRECTION}", "{CONTEXT_BRIEFING}"]

# Minimum prompt length that can meaningfully specify tone, opening, pushback, and avoids
MIN_PROMPT_LENGTH = 300


def all_strategy_ids() -> list[str]:
    return list_all("strategies")


def all_persona_ids() -> list[str]:
    return list_all("personas")


@pytest.mark.parametrize("strategy_id", all_strategy_ids())
class TestStrategyDataQuality:
    def test_id_matches_filename(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        assert strategy.id == strategy_id, (
            f"Strategy id field '{strategy.id}' does not match filename '{strategy_id}'"
        )

    def test_display_name_is_non_empty(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        assert strategy.display_name.strip(), f"{strategy_id}: display_name must not be empty"

    def test_one_line_description_is_non_empty(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        assert strategy.one_line_description.strip(), (
            f"{strategy_id}: one_line_description must not be empty"
        )

    def test_academic_citation_has_framework_and_source(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        assert strategy.academic_citation.framework.strip(), (
            f"{strategy_id}: academic_citation.framework must not be empty"
        )
        assert strategy.academic_citation.primary_source.strip(), (
            f"{strategy_id}: academic_citation.primary_source must not be empty"
        )

    def test_persuader_prompt_minimum_length(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        assert len(strategy.persuader_system_prompt) >= MIN_PROMPT_LENGTH, (
            f"{strategy_id}: persuader_system_prompt too short "
            f"(got {len(strategy.persuader_system_prompt)} chars, need >= {MIN_PROMPT_LENGTH})"
        )

    def test_persuader_prompt_contains_required_slots(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        for slot in REQUIRED_TEMPLATE_SLOTS:
            assert slot in strategy.persuader_system_prompt, (
                f"{strategy_id}: persuader_system_prompt missing template slot '{slot}'"
            )

    def test_predicted_effective_on_references_valid_personas(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        valid_ids = set(all_persona_ids())
        for persona_id in strategy.predicted_effective_on:
            assert persona_id in valid_ids, (
                f"{strategy_id}: predicted_effective_on references unknown persona '{persona_id}'"
            )

    def test_predicted_ineffective_on_references_valid_personas(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        valid_ids = set(all_persona_ids())
        for persona_id in strategy.predicted_ineffective_on:
            assert persona_id in valid_ids, (
                f"{strategy_id}: predicted_ineffective_on references unknown persona '{persona_id}'"
            )

    def test_no_overlap_between_effective_and_ineffective(self, strategy_id: str) -> None:
        strategy = load_strategy(strategy_id)
        effective = set(strategy.predicted_effective_on)
        ineffective = set(strategy.predicted_ineffective_on)
        overlap = effective & ineffective
        assert not overlap, (
            f"{strategy_id}: same persona(s) in both predicted_effective_on and "
            f"predicted_ineffective_on: {overlap}"
        )
