"""
Tests for ai_analyzer — response parsing and prompt construction.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from shared import ai_analyzer


VALID_AI_RESPONSE = {
    "summary": "The Docker build failed because the base image tag no longer exists.",
    "root_cause": "The pinned base image `python:3.11.0-slim` was removed from Docker Hub.",
    "affected_steps": ["Build Docker Image", "Push to ACR"],
    "error_snippets": [
        "ERROR: failed to solve: python:3.11.0-slim: not found",
        "Build failed with exit code 1",
    ],
    "recommendations": [
        {
            "title": "Update base image tag",
            "description": "Change Dockerfile FROM to python:3.11-slim (unpinned patch) or a digest.",
            "priority": "high",
        }
    ],
    "severity": "high",
    "confidence": 0.95,
}


def _mock_openai_response(content: str):
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


class TestAnalyzePipelineRun:
    @patch("shared.ai_analyzer.AzureOpenAI")
    def test_valid_response_parsed_correctly(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            json.dumps(VALID_AI_RESPONSE)
        )

        result = ai_analyzer.analyze_pipeline_run(
            pipeline_name="backend-ci",
            project_name="MyProject",
            build_number="20240101.5",
            result="failed",
            branch="refs/heads/main",
            duration_seconds=270,
            failed_steps=[{"name": "Build Docker Image", "result": "failed", "errorCount": 1}],
            logs="ERROR: failed to solve: python:3.11.0-slim: not found",
        )

        assert result["summary"] == VALID_AI_RESPONSE["summary"]
        assert result["severity"] == "high"
        assert result["confidence"] == 0.95
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["priority"] == "high"

    @patch("shared.ai_analyzer.AzureOpenAI")
    def test_malformed_json_returns_fallback(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            "Sorry, I can't analyze that right now."
        )

        result = ai_analyzer.analyze_pipeline_run(
            pipeline_name="backend-ci",
            project_name="MyProject",
            build_number="20240101.5",
            result="failed",
            branch="main",
            duration_seconds=0,
            failed_steps=[],
            logs="",
        )

        assert result["confidence"] == 0.0
        assert result["severity"] == "high"
        assert result["recommendations"] == []

    @patch("shared.ai_analyzer.AzureOpenAI")
    def test_long_logs_are_truncated(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            json.dumps(VALID_AI_RESPONSE)
        )

        long_logs = "line\n" * 5000  # ~25 KB

        ai_analyzer.analyze_pipeline_run(
            pipeline_name="p",
            project_name="proj",
            build_number="1.0",
            result="failed",
            branch="main",
            duration_seconds=60,
            failed_steps=[],
            logs=long_logs,
        )

        call_args = mock_client.chat.completions.create.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        # Logs are capped at 12000 chars in the prompt
        assert len(user_message) < 15000

    @patch("shared.ai_analyzer.AzureOpenAI")
    def test_duration_formatted_as_minutes(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            json.dumps(VALID_AI_RESPONSE)
        )

        ai_analyzer.analyze_pipeline_run(
            pipeline_name="p",
            project_name="proj",
            build_number="1.0",
            result="failed",
            branch="main",
            duration_seconds=150,
            failed_steps=[],
            logs="",
        )

        call_args = mock_client.chat.completions.create.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        assert "2m 30s" in user_message

    @patch("shared.ai_analyzer.AzureOpenAI")
    def test_failed_steps_appear_in_prompt(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            json.dumps(VALID_AI_RESPONSE)
        )

        ai_analyzer.analyze_pipeline_run(
            pipeline_name="p",
            project_name="proj",
            build_number="1.0",
            result="failed",
            branch="main",
            duration_seconds=0,
            failed_steps=[{"name": "Run Tests", "result": "failed", "errorCount": 3}],
            logs="",
        )

        call_args = mock_client.chat.completions.create.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        assert "Run Tests" in user_message
