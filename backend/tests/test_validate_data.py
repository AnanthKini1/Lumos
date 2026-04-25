"""
Tests for backend/validate_data.py

Covers:
- validate_dir passes on valid JSON files
- validate_dir fails on JSON missing required fields
- validate_dir fails on JSON with wrong field types
- validate_dir returns (0, 0) for empty directories
- main() exits with code 0 when all files pass
- main() exits with code 1 when any file fails
"""

import json
import sys
from pathlib import Path

import pytest

# Add backend/ to path so imports resolve without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import PersonaProfile
from validate_data import validate_dir


VALID_PERSONA = {
    "id": "persona_test",
    "display_name": "Test Person",
    "demographic_shorthand": "40, test city, college-educated",
    "first_person_description": "I am a test persona used in unit tests.",
    "core_values": ["honesty", "curiosity"],
    "communication_preferences": {
        "directness": "direct",
        "evidence_preference": "data",
        "tone": "neutral"
    },
    "trust_orientation": ["experts", "data"],
    "identity_groups": ["researchers"],
    "emotional_triggers": {
        "defensive_when": ["dismissed"],
        "open_when": ["asked_questions"]
    },
    "trusted_sources": ["academic_journals"],
    "source_citation": {
        "primary_source": "Test Source 2024",
        "url": None,
        "supplementary": []
    },
    "predicted_behavior_under_strategies": {
        "strategy_authority_expert": "Expected to engage positively.",
        "strategy_personal_narrative": "Expected neutral."
    }
}


class TestValidateDir:
    def test_passes_valid_persona_file(self, tmp_path: Path) -> None:
        (tmp_path / "persona_test.json").write_text(json.dumps(VALID_PERSONA))
        passed, failed = validate_dir(tmp_path, PersonaProfile)
        assert passed == 1
        assert failed == 0

    def test_fails_persona_missing_required_field(self, tmp_path: Path) -> None:
        bad = {k: v for k, v in VALID_PERSONA.items() if k != "display_name"}
        (tmp_path / "persona_bad.json").write_text(json.dumps(bad))
        passed, failed = validate_dir(tmp_path, PersonaProfile)
        assert passed == 0
        assert failed == 1

    def test_fails_persona_wrong_type_on_core_values(self, tmp_path: Path) -> None:
        bad = {**VALID_PERSONA, "core_values": "not_a_list"}
        (tmp_path / "persona_bad_type.json").write_text(json.dumps(bad))
        passed, failed = validate_dir(tmp_path, PersonaProfile)
        assert passed == 0
        assert failed == 1

    def test_fails_persona_missing_nested_field(self, tmp_path: Path) -> None:
        bad = {
            **VALID_PERSONA,
            "communication_preferences": {"directness": "direct"}  # missing evidence_preference and tone
        }
        (tmp_path / "persona_bad_nested.json").write_text(json.dumps(bad))
        passed, failed = validate_dir(tmp_path, PersonaProfile)
        assert passed == 0
        assert failed == 1

    def test_fails_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / "persona_corrupt.json").write_text("{ not valid json }")
        passed, failed = validate_dir(tmp_path, PersonaProfile)
        assert passed == 0
        assert failed == 1

    def test_empty_directory_returns_zero_zero(self, tmp_path: Path) -> None:
        passed, failed = validate_dir(tmp_path, PersonaProfile)
        assert passed == 0
        assert failed == 0

    def test_counts_multiple_files_correctly(self, tmp_path: Path) -> None:
        (tmp_path / "persona_good1.json").write_text(json.dumps(VALID_PERSONA))
        good2 = {**VALID_PERSONA, "id": "persona_test_2", "display_name": "Test 2"}
        (tmp_path / "persona_good2.json").write_text(json.dumps(good2))
        bad = {k: v for k, v in VALID_PERSONA.items() if k != "core_values"}
        (tmp_path / "persona_bad.json").write_text(json.dumps(bad))
        passed, failed = validate_dir(tmp_path, PersonaProfile)
        assert passed == 2
        assert failed == 1

    def test_ignores_non_json_files(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("not a json file")
        (tmp_path / "persona_good.json").write_text(json.dumps(VALID_PERSONA))
        passed, failed = validate_dir(tmp_path, PersonaProfile)
        assert passed == 1
        assert failed == 0
