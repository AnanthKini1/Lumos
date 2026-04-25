"""
Tests for judge_agent.run_judge_call.

Uses unittest.mock to patch the Anthropic client — no real API calls made.
"""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from measurement.judge_agent import JudgeResult, run_judge_call


def _make_mock_message(response_dict: dict) -> MagicMock:
    """Build a mock Anthropic message response with the given JSON payload."""
    content_block = MagicMock()
    content_block.text = json.dumps(response_dict)
    message = MagicMock()
    message.content = [content_block]
    return message


VALID_RESPONSE = {"score": 7.5, "evidence_quotes": ["quote one", "quote two"]}
SAMPLE_PROMPT = "DIMENSION: TEST\nDEFINITION: Test prompt."
SAMPLE_TRANSCRIPT = json.dumps({"turn": 1, "persona_output": {"private_stance": 4.0}})


@pytest.fixture()
def mock_anthropic_client():
    """Patch AsyncAnthropic so no network calls are made."""
    with patch("measurement.judge_agent.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        yield mock_client


class TestRunJudgeCallHappyPath:
    @pytest.mark.asyncio
    async def test_returns_judge_result(self, mock_anthropic_client: AsyncMock) -> None:
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=_make_mock_message(VALID_RESPONSE)
        )
        result = await run_judge_call(SAMPLE_PROMPT, SAMPLE_TRANSCRIPT)
        assert result["score"] == 7.5
        assert result["evidence_quotes"] == ["quote one", "quote two"]

    @pytest.mark.asyncio
    async def test_score_is_float(self, mock_anthropic_client: AsyncMock) -> None:
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=_make_mock_message({"score": 5, "evidence_quotes": ["q"]})
        )
        result = await run_judge_call(SAMPLE_PROMPT, SAMPLE_TRANSCRIPT)
        assert isinstance(result["score"], float)

    @pytest.mark.asyncio
    async def test_passes_prompt_as_system(self, mock_anthropic_client: AsyncMock) -> None:
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=_make_mock_message(VALID_RESPONSE)
        )
        await run_judge_call(SAMPLE_PROMPT, SAMPLE_TRANSCRIPT)
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == SAMPLE_PROMPT

    @pytest.mark.asyncio
    async def test_transcript_in_user_message(self, mock_anthropic_client: AsyncMock) -> None:
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=_make_mock_message(VALID_RESPONSE)
        )
        await run_judge_call(SAMPLE_PROMPT, SAMPLE_TRANSCRIPT)
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        user_content = call_kwargs["messages"][0]["content"]
        assert SAMPLE_TRANSCRIPT in user_content

    @pytest.mark.asyncio
    async def test_enforces_max_tokens_cap(self, mock_anthropic_client: AsyncMock) -> None:
        from config import MAX_TOKENS_JUDGE

        mock_anthropic_client.messages.create = AsyncMock(
            return_value=_make_mock_message(VALID_RESPONSE)
        )
        await run_judge_call(SAMPLE_PROMPT, SAMPLE_TRANSCRIPT)
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == MAX_TOKENS_JUDGE


class TestRunJudgeCallErrorHandling:
    @pytest.mark.asyncio
    async def test_raises_on_invalid_json(self, mock_anthropic_client: AsyncMock) -> None:
        content_block = MagicMock()
        content_block.text = "not json at all"
        message = MagicMock()
        message.content = [content_block]
        mock_anthropic_client.messages.create = AsyncMock(return_value=message)

        with pytest.raises(ValueError, match="not valid JSON"):
            await run_judge_call(SAMPLE_PROMPT, SAMPLE_TRANSCRIPT)

    @pytest.mark.asyncio
    async def test_raises_on_missing_score_key(self, mock_anthropic_client: AsyncMock) -> None:
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=_make_mock_message({"evidence_quotes": ["q"]})
        )
        with pytest.raises(ValueError, match="missing required keys"):
            await run_judge_call(SAMPLE_PROMPT, SAMPLE_TRANSCRIPT)

    @pytest.mark.asyncio
    async def test_raises_on_missing_evidence_quotes_key(
        self, mock_anthropic_client: AsyncMock
    ) -> None:
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=_make_mock_message({"score": 5.0})
        )
        with pytest.raises(ValueError, match="missing required keys"):
            await run_judge_call(SAMPLE_PROMPT, SAMPLE_TRANSCRIPT)
