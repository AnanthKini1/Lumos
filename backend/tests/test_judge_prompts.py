"""
Tests for judge_prompts.py — validates that all 7 prompt strings are
well-formed and contain the required structural elements.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from measurement.judge_prompts import (
    ALL_PROMPTS,
    AMBIVALENCE_PRESENCE_PROMPT,
    ENGAGEMENT_DEPTH_PROMPT,
    IDENTITY_THREAT_PROMPT,
    MEMORY_RESIDUE_PROMPT,
    MOTIVATED_REASONING_PROMPT,
    PERSISTENCE_PROMPT,
    PUBLIC_PRIVATE_GAP_PROMPT,
)

EXPECTED_KEYS = {
    "public_private_gap",
    "identity_threat",
    "motivated_reasoning",
    "engagement_depth",
    "ambivalence_presence",
    "memory_residue",
    "persistence",
}

REQUIRED_FIELDS_IN_PROMPT = [
    "internal_monologue",
    "emotional_reaction",
    "identity_threat",
    "private_stance",
    "memory_to_carry_forward",
    "public_response",
]

REQUIRED_JSON_OUTPUT_KEYS = ['"score"', '"evidence_quotes"']


class TestAllPromptsDict:
    def test_all_keys_present(self) -> None:
        assert set(ALL_PROMPTS.keys()) == EXPECTED_KEYS

    def test_all_values_non_empty(self) -> None:
        for key, prompt in ALL_PROMPTS.items():
            assert prompt.strip(), f"ALL_PROMPTS['{key}'] is empty"

    def test_all_prompts_match_constants(self) -> None:
        assert ALL_PROMPTS["public_private_gap"] == PUBLIC_PRIVATE_GAP_PROMPT
        assert ALL_PROMPTS["identity_threat"] == IDENTITY_THREAT_PROMPT
        assert ALL_PROMPTS["motivated_reasoning"] == MOTIVATED_REASONING_PROMPT
        assert ALL_PROMPTS["engagement_depth"] == ENGAGEMENT_DEPTH_PROMPT
        assert ALL_PROMPTS["ambivalence_presence"] == AMBIVALENCE_PRESENCE_PROMPT
        assert ALL_PROMPTS["memory_residue"] == MEMORY_RESIDUE_PROMPT
        assert ALL_PROMPTS["persistence"] == PERSISTENCE_PROMPT


@pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
class TestPromptQuality:
    def test_minimum_length(self, key: str) -> None:
        prompt = ALL_PROMPTS[key]
        assert len(prompt) >= 300, (
            f"Prompt '{key}' is too short ({len(prompt)} chars, need >= 300)"
        )

    def test_references_transcript_fields(self, key: str) -> None:
        prompt = ALL_PROMPTS[key]
        for field in REQUIRED_FIELDS_IN_PROMPT:
            assert field in prompt, (
                f"Prompt '{key}' does not reference required field '{field}'"
            )

    def test_specifies_json_output(self, key: str) -> None:
        prompt = ALL_PROMPTS[key]
        for json_key in REQUIRED_JSON_OUTPUT_KEYS:
            assert json_key in prompt, (
                f"Prompt '{key}' missing required JSON output key {json_key}"
            )

    def test_has_scoring_guide(self, key: str) -> None:
        prompt = ALL_PROMPTS[key]
        assert "Score 0-3" in prompt or "Score 0" in prompt, (
            f"Prompt '{key}' appears to be missing a scoring guide"
        )

    def test_has_definition_section(self, key: str) -> None:
        prompt = ALL_PROMPTS[key]
        assert "DEFINITION" in prompt, (
            f"Prompt '{key}' is missing a DEFINITION section"
        )
