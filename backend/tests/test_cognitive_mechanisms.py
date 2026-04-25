"""
Tests for the cognitive mechanisms library and its loader.

Covers:
- load_cognitive_mechanisms() returns the inner array, not the wrapper object
- Correct count and structure of mechanisms
- Every mechanism has all required fields with non-empty values
- category is one of the three valid values
- IDs are unique and follow the naming convention
- scoring_anchor has low/mid/high keys
- citations array is non-empty with verbatim quotes
- behavioral_signals and diagnostic_indicators are non-empty lists
- Specific known mechanism IDs are present
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loader import load_cognitive_mechanisms

REQUIRED_MECHANISM_FIELDS = [
    "id",
    "display_name",
    "framework",
    "category",
    "operational_definition",
    "behavioral_signals",
    "diagnostic_indicators",
    "scoring_anchor",
    "citations",
]

VALID_CATEGORIES = {"backfire", "genuine_persuasion", "surface_mechanism"}

KNOWN_MECHANISM_IDS = [
    "mechanism_identity_protective_cognition",
    "mechanism_reactance",
    "mechanism_narrative_transportation",
    "mechanism_central_route_elaboration",
    "mechanism_peripheral_route_compliance",
    "mechanism_source_credibility_discounting",
]


@pytest.fixture(scope="module")
def mechanisms() -> list[dict]:
    return load_cognitive_mechanisms()


class TestLoaderReturnsArray:
    def test_returns_list_not_dict(self, mechanisms: list[dict]) -> None:
        assert isinstance(mechanisms, list), (
            "load_cognitive_mechanisms() must return a list, not the wrapper object. "
            "The JSON wraps mechanisms in {version, mechanisms[]} — "
            "loader must return data['mechanisms']."
        )

    def test_list_is_non_empty(self, mechanisms: list[dict]) -> None:
        assert len(mechanisms) > 0

    def test_returns_at_least_six_mechanisms(self, mechanisms: list[dict]) -> None:
        assert len(mechanisms) >= 6, (
            f"Expected at least 6 mechanisms, got {len(mechanisms)}"
        )

    def test_elements_are_dicts(self, mechanisms: list[dict]) -> None:
        for m in mechanisms:
            assert isinstance(m, dict), f"Each mechanism must be a dict, got {type(m)}"


class TestMechanismPresence:
    def test_known_ids_are_present(self, mechanisms: list[dict]) -> None:
        ids = {m["id"] for m in mechanisms}
        for known_id in KNOWN_MECHANISM_IDS:
            assert known_id in ids, f"Expected mechanism '{known_id}' not found in library"

    def test_ids_are_unique(self, mechanisms: list[dict]) -> None:
        ids = [m["id"] for m in mechanisms]
        assert len(ids) == len(set(ids)), "Mechanism IDs must be unique"

    def test_ids_follow_naming_convention(self, mechanisms: list[dict]) -> None:
        for m in mechanisms:
            assert m["id"].startswith("mechanism_"), (
                f"ID '{m['id']}' must start with 'mechanism_'"
            )


@pytest.mark.parametrize(
    "mechanism_id",
    [m["id"] for m in load_cognitive_mechanisms()],
)
class TestMechanismFieldCompleteness:
    def _get(self, mechanism_id: str) -> dict:
        return next(m for m in load_cognitive_mechanisms() if m["id"] == mechanism_id)

    def test_has_all_required_fields(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        for field in REQUIRED_MECHANISM_FIELDS:
            assert field in m, f"{mechanism_id}: missing required field '{field}'"

    def test_id_is_non_empty_string(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        assert isinstance(m["id"], str) and m["id"].strip()

    def test_display_name_is_non_empty(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        assert isinstance(m["display_name"], str) and m["display_name"].strip(), (
            f"{mechanism_id}: display_name must be a non-empty string"
        )

    def test_framework_is_non_empty(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        assert isinstance(m["framework"], str) and m["framework"].strip(), (
            f"{mechanism_id}: framework must reference an academic source"
        )

    def test_category_is_valid(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        assert m["category"] in VALID_CATEGORIES, (
            f"{mechanism_id}: category '{m['category']}' must be one of {VALID_CATEGORIES}"
        )

    def test_operational_definition_is_substantive(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        assert len(m["operational_definition"]) >= 50, (
            f"{mechanism_id}: operational_definition too short "
            f"(got {len(m['operational_definition'])} chars)"
        )

    def test_behavioral_signals_is_non_empty_list(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        assert isinstance(m["behavioral_signals"], list), (
            f"{mechanism_id}: behavioral_signals must be a list"
        )
        assert len(m["behavioral_signals"]) >= 1, (
            f"{mechanism_id}: behavioral_signals must have at least one entry"
        )

    def test_behavioral_signals_are_strings(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        for sig in m["behavioral_signals"]:
            assert isinstance(sig, str) and sig.strip(), (
                f"{mechanism_id}: each behavioral_signal must be a non-empty string"
            )

    def test_diagnostic_indicators_is_non_empty_list(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        assert isinstance(m["diagnostic_indicators"], list), (
            f"{mechanism_id}: diagnostic_indicators must be a list"
        )
        assert len(m["diagnostic_indicators"]) >= 1, (
            f"{mechanism_id}: diagnostic_indicators must have at least one entry"
        )

    def test_diagnostic_indicators_are_strings(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        for ind in m["diagnostic_indicators"]:
            assert isinstance(ind, str) and ind.strip(), (
                f"{mechanism_id}: each diagnostic_indicator must be a non-empty string"
            )

    def test_scoring_anchor_has_required_keys(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        anchor = m["scoring_anchor"]
        assert isinstance(anchor, dict), f"{mechanism_id}: scoring_anchor must be a dict"
        for key in ("low", "mid", "high"):
            assert key in anchor, f"{mechanism_id}: scoring_anchor missing '{key}' key"
            assert isinstance(anchor[key], str) and anchor[key].strip(), (
                f"{mechanism_id}: scoring_anchor['{key}'] must be a non-empty string"
            )

    def test_citations_is_non_empty_list(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        assert isinstance(m["citations"], list), (
            f"{mechanism_id}: citations must be a list"
        )
        assert len(m["citations"]) >= 1, (
            f"{mechanism_id}: must have at least one citation"
        )

    def test_citations_have_direct_quotes(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        for i, cite in enumerate(m["citations"]):
            assert "direct_quote" in cite, (
                f"{mechanism_id}: citation[{i}] missing 'direct_quote'"
            )
            assert isinstance(cite["direct_quote"], str) and cite["direct_quote"].strip(), (
                f"{mechanism_id}: citation[{i}].direct_quote must be a non-empty string"
            )

    def test_citations_have_author_and_year(self, mechanism_id: str) -> None:
        m = self._get(mechanism_id)
        for i, cite in enumerate(m["citations"]):
            assert "author" in cite and cite["author"].strip(), (
                f"{mechanism_id}: citation[{i}] missing 'author'"
            )
            assert "year" in cite and isinstance(cite["year"], int), (
                f"{mechanism_id}: citation[{i}] 'year' must be an integer"
            )


class TestCategoryDistribution:
    def test_at_least_one_backfire_mechanism(self, mechanisms: list[dict]) -> None:
        backfires = [m for m in mechanisms if m["category"] == "backfire"]
        assert len(backfires) >= 1, "Library must contain at least one backfire mechanism"

    def test_at_least_one_genuine_persuasion_mechanism(self, mechanisms: list[dict]) -> None:
        genuine = [m for m in mechanisms if m["category"] == "genuine_persuasion"]
        assert len(genuine) >= 1, "Library must contain at least one genuine_persuasion mechanism"

    def test_at_least_one_surface_mechanism(self, mechanisms: list[dict]) -> None:
        surface = [m for m in mechanisms if m["category"] == "surface_mechanism"]
        assert len(surface) >= 1, "Library must contain at least one surface_mechanism"
