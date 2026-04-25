"""
Tests for backend/agents/mechanism_agent.py.

Pure Python — no real API calls. Covers:

_build_mechanism_context():
- Returns a string
- Contains each mechanism's ID
- Contains each mechanism's display_name
- Contains behavioral_signals entries for each mechanism
- Contains diagnostic_indicators entries for each mechanism
- Contains scoring_anchor LOW and HIGH text
- Does NOT include raw citation direct_quote text (too many tokens for judge)
- Handles mechanisms with missing optional fields (no KeyError)
- Starts with "COGNITIVE MECHANISM LIBRARY:"

classify_mechanism() — with mocked AsyncAnthropic:
- Returns a MechanismClassification instance
- primary_mechanism_id is one of the valid IDs from the library
- color_category matches the category of the primary mechanism
- intensity is derived from stance_delta / 10.0, clamped to [0, 1]
- evidence_quotes is a list of non-empty strings (empty strings filtered)
- secondary_mechanism_id is None when model returns empty string
- secondary_mechanism_id is set when model returns a valid ID
- Fallback fires and returns a valid ID when model returns unrecognized mechanism ID
  - positive delta (moved away) → falls back to a "backfire" category mechanism
  - negative delta (moved toward) → falls back to a "genuine_persuasion" category mechanism
- ValueError raised when model returns no tool_use block
- Large stance_delta (>10) intensity is clamped to 1.0
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.mechanism_agent import _build_mechanism_context, classify_mechanism
from models import MechanismClassification


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_MINIMAL_MECHANISM = {
    "id": "mechanism_test_alpha",
    "display_name": "Test Alpha",
    "framework": "Author, 2000",
    "category": "backfire",
    "operational_definition": "A test mechanism for unit tests.",
    "behavioral_signals": ["signal one", "signal two"],
    "diagnostic_indicators": ["indicator alpha", "indicator beta"],
    "scoring_anchor": {"low": "low description", "mid": "mid description", "high": "high description"},
    "citations": [
        {
            "direct_quote": "verbatim quote from paper",
            "author": "Author",
            "year": 2000,
            "source": "Journal",
            "page_or_section": "p. 1",
        }
    ],
}

_MINIMAL_MECHANISM_2 = {
    "id": "mechanism_test_beta",
    "display_name": "Test Beta",
    "framework": "Author B, 2001",
    "category": "genuine_persuasion",
    "operational_definition": "Another test mechanism for unit tests.",
    "behavioral_signals": ["beta signal"],
    "diagnostic_indicators": ["beta indicator"],
    "scoring_anchor": {"low": "beta low", "mid": "beta mid", "high": "beta high"},
    "citations": [
        {
            "direct_quote": "another verbatim quote",
            "author": "Author B",
            "year": 2001,
            "source": "Conference",
            "page_or_section": "p. 5",
        }
    ],
}

_TWO_MECHANISMS = [_MINIMAL_MECHANISM, _MINIMAL_MECHANISM_2]


# ---------------------------------------------------------------------------
# _build_mechanism_context — structure tests
# ---------------------------------------------------------------------------

class TestBuildMechanismContext:
    def test_returns_string(self) -> None:
        result = _build_mechanism_context(_TWO_MECHANISMS)
        assert isinstance(result, str)

    def test_starts_with_header(self) -> None:
        result = _build_mechanism_context(_TWO_MECHANISMS)
        assert result.startswith("COGNITIVE MECHANISM LIBRARY:")

    def test_contains_each_mechanism_id(self) -> None:
        result = _build_mechanism_context(_TWO_MECHANISMS)
        for m in _TWO_MECHANISMS:
            assert m["id"] in result, f"Expected ID '{m['id']}' in context"

    def test_contains_each_display_name(self) -> None:
        result = _build_mechanism_context(_TWO_MECHANISMS)
        for m in _TWO_MECHANISMS:
            assert m["display_name"] in result, f"Expected display_name '{m['display_name']}' in context"

    def test_contains_behavioral_signals(self) -> None:
        result = _build_mechanism_context(_TWO_MECHANISMS)
        assert "signal one" in result
        assert "signal two" in result
        assert "beta signal" in result

    def test_contains_diagnostic_indicators(self) -> None:
        result = _build_mechanism_context(_TWO_MECHANISMS)
        assert "indicator alpha" in result
        assert "beta indicator" in result

    def test_contains_scoring_anchor_low_and_high(self) -> None:
        result = _build_mechanism_context(_TWO_MECHANISMS)
        assert "low description" in result
        assert "high description" in result
        assert "beta low" in result
        assert "beta high" in result

    def test_does_not_contain_verbatim_citation_quotes(self) -> None:
        # Citations are for frontend display only — too many tokens for the judge
        result = _build_mechanism_context(_TWO_MECHANISMS)
        assert "verbatim quote from paper" not in result
        assert "another verbatim quote" not in result

    def test_handles_missing_behavioral_signals_gracefully(self) -> None:
        mechanism_no_signals = {**_MINIMAL_MECHANISM, "behavioral_signals": []}
        result = _build_mechanism_context([mechanism_no_signals])
        assert isinstance(result, str)  # no crash

    def test_handles_missing_scoring_anchor_gracefully(self) -> None:
        mechanism_no_anchor = {k: v for k, v in _MINIMAL_MECHANISM.items() if k != "scoring_anchor"}
        result = _build_mechanism_context([mechanism_no_anchor])
        assert isinstance(result, str)

    def test_empty_mechanisms_returns_header_only(self) -> None:
        result = _build_mechanism_context([])
        assert result == "COGNITIVE MECHANISM LIBRARY:"

    def test_contains_framework_reference(self) -> None:
        result = _build_mechanism_context(_TWO_MECHANISMS)
        assert "Author, 2000" in result
        assert "Author B, 2001" in result

    def test_real_mechanisms_library_produces_valid_context(self) -> None:
        from data.loader import load_cognitive_mechanisms
        mechanisms = load_cognitive_mechanisms()
        result = _build_mechanism_context(mechanisms)
        assert isinstance(result, str)
        assert len(result) > 500  # substantive content
        for m in mechanisms:
            assert m["id"] in result


# ---------------------------------------------------------------------------
# Helpers for mocking the Anthropic client
# ---------------------------------------------------------------------------

def _make_tool_block(input_dict: dict) -> SimpleNamespace:
    block = SimpleNamespace()
    block.type = "tool_use"
    block.input = input_dict
    return block


def _make_text_block(text: str = "ok") -> SimpleNamespace:
    block = SimpleNamespace()
    block.type = "text"
    block.text = text
    return block


def _make_response(tool_input: dict | None) -> MagicMock:
    resp = MagicMock()
    if tool_input is not None:
        resp.content = [_make_tool_block(tool_input)]
    else:
        resp.content = [_make_text_block()]
    return resp


def _tool_input(
    primary: str = "mechanism_test_alpha",
    secondary: str = "",
    explanation: str = "Because of X.",
    quote1: str = "I felt defensive",
    quote2: str = "",
) -> dict:
    return {
        "primary_mechanism_id": primary,
        "secondary_mechanism_id": secondary,
        "explanation": explanation,
        "evidence_quote_1": quote1,
        "evidence_quote_2": quote2,
    }


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# classify_mechanism — happy path
# ---------------------------------------------------------------------------

class TestClassifyMechanismHappyPath:
    def _call(self, tool_input: dict, delta: float = 2.0) -> MechanismClassification:
        mock_response = _make_response(tool_input)
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_async_anthropic = MagicMock(return_value=mock_client)

        with patch("agents.mechanism_agent.anthropic.AsyncAnthropic", mock_async_anthropic):
            return _run(
                classify_mechanism(
                    persuader_phrase="You should think about this.",
                    persona_monologue="I am not sure anymore.",
                    stance_delta=delta,
                    mechanisms=_TWO_MECHANISMS,
                )
            )

    def test_returns_mechanism_classification(self) -> None:
        result = self._call(_tool_input())
        assert isinstance(result, MechanismClassification)

    def test_primary_mechanism_id_is_valid(self) -> None:
        result = self._call(_tool_input(primary="mechanism_test_alpha"))
        assert result.primary_mechanism_id == "mechanism_test_alpha"

    def test_color_category_matches_primary_mechanism(self) -> None:
        # mechanism_test_alpha has category "backfire"
        result = self._call(_tool_input(primary="mechanism_test_alpha"))
        assert result.color_category == "backfire"

    def test_color_category_genuine_persuasion(self) -> None:
        result = self._call(_tool_input(primary="mechanism_test_beta"))
        assert result.color_category == "genuine_persuasion"

    def test_intensity_derived_from_delta(self) -> None:
        result = self._call(_tool_input(), delta=3.0)
        assert result.intensity == pytest.approx(0.3)

    def test_intensity_negative_delta_uses_abs(self) -> None:
        result = self._call(_tool_input(), delta=-4.0)
        assert result.intensity == pytest.approx(0.4)

    def test_intensity_clamped_to_one_for_large_delta(self) -> None:
        result = self._call(_tool_input(), delta=15.0)
        assert result.intensity == pytest.approx(1.0)

    def test_secondary_mechanism_id_none_when_empty_string(self) -> None:
        result = self._call(_tool_input(secondary=""))
        assert result.secondary_mechanism_id is None

    def test_secondary_mechanism_id_set_when_valid(self) -> None:
        result = self._call(_tool_input(secondary="mechanism_test_beta"))
        assert result.secondary_mechanism_id == "mechanism_test_beta"

    def test_secondary_mechanism_id_none_when_invalid(self) -> None:
        result = self._call(_tool_input(secondary="mechanism_nonexistent"))
        assert result.secondary_mechanism_id is None

    def test_evidence_quotes_include_non_empty_strings(self) -> None:
        result = self._call(_tool_input(quote1="phrase one", quote2="phrase two"))
        assert "phrase one" in result.evidence_quotes
        assert "phrase two" in result.evidence_quotes

    def test_evidence_quotes_filter_empty_strings(self) -> None:
        result = self._call(_tool_input(quote1="phrase one", quote2=""))
        assert result.evidence_quotes == ["phrase one"]

    def test_evidence_quotes_both_empty_returns_empty_list(self) -> None:
        result = self._call(_tool_input(quote1="", quote2=""))
        assert result.evidence_quotes == []

    def test_explanation_is_preserved(self) -> None:
        result = self._call(_tool_input(explanation="This is the explanation."))
        assert result.explanation == "This is the explanation."


# ---------------------------------------------------------------------------
# classify_mechanism — fallback behavior
# ---------------------------------------------------------------------------

class TestClassifyMechanismFallback:
    def _call_with_invalid_primary(self, delta: float) -> MechanismClassification:
        tool_input = _tool_input(primary="mechanism_does_not_exist")
        mock_response = _make_response(tool_input)
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_async_anthropic = MagicMock(return_value=mock_client)

        with patch("agents.mechanism_agent.anthropic.AsyncAnthropic", mock_async_anthropic):
            return _run(
                classify_mechanism(
                    persuader_phrase="Test phrase.",
                    persona_monologue="Test monologue.",
                    stance_delta=delta,
                    mechanisms=_TWO_MECHANISMS,
                )
            )

    def test_fallback_returns_valid_mechanism_id_on_invalid_primary(self) -> None:
        valid_ids = {m["id"] for m in _TWO_MECHANISMS}
        result = self._call_with_invalid_primary(delta=2.0)
        assert result.primary_mechanism_id in valid_ids

    def test_fallback_positive_delta_picks_backfire_category(self) -> None:
        # positive delta = moved away from persuader's position → backfire
        result = self._call_with_invalid_primary(delta=2.0)
        assert result.color_category == "backfire"
        assert result.primary_mechanism_id == "mechanism_test_alpha"

    def test_fallback_negative_delta_picks_genuine_persuasion_category(self) -> None:
        # negative delta = moved toward persuader's position → genuine_persuasion
        result = self._call_with_invalid_primary(delta=-2.0)
        assert result.color_category == "genuine_persuasion"
        assert result.primary_mechanism_id == "mechanism_test_beta"

    def test_fallback_uses_first_mechanism_when_no_category_match(self) -> None:
        # Only surface_mechanism available — no backfire, no genuine_persuasion
        surface_only = [
            {**_MINIMAL_MECHANISM, "id": "mechanism_surface", "category": "surface_mechanism"}
        ]
        tool_input = _tool_input(primary="mechanism_does_not_exist")
        mock_response = _make_response(tool_input)
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("agents.mechanism_agent.anthropic.AsyncAnthropic", MagicMock(return_value=mock_client)):
            result = _run(
                classify_mechanism(
                    persuader_phrase="phrase",
                    persona_monologue="monologue",
                    stance_delta=2.0,
                    mechanisms=surface_only,
                )
            )

        assert result.primary_mechanism_id == "mechanism_surface"


# ---------------------------------------------------------------------------
# classify_mechanism — error path
# ---------------------------------------------------------------------------

class TestClassifyMechanismErrorPath:
    def test_raises_value_error_when_no_tool_block(self) -> None:
        mock_response = _make_response(None)  # text block only, no tool_use
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("agents.mechanism_agent.anthropic.AsyncAnthropic", MagicMock(return_value=mock_client)):
            with pytest.raises(ValueError, match="did not invoke tool"):
                _run(
                    classify_mechanism(
                        persuader_phrase="phrase",
                        persona_monologue="monologue",
                        stance_delta=1.5,
                        mechanisms=_TWO_MECHANISMS,
                    )
                )
