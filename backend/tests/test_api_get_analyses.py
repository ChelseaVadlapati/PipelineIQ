"""
Tests for api_get_analyses — query parameter parsing and response shape.
"""

import json
import pytest
from unittest.mock import patch

import azure.functions as func

from api_get_analyses import main, _int_param


SAMPLE_ANALYSES = [
    {
        "id": "a1",
        "type": "analysis",
        "pipeline_name": "backend-ci",
        "project_name": "MyProject",
        "result": "failed",
        "severity": "high",
        "summary": "Build failed due to missing dependency.",
        "analyzed_at": "2024-01-01T10:00:00",
    },
    {
        "id": "a2",
        "type": "analysis",
        "pipeline_name": "frontend-ci",
        "project_name": "MyProject",
        "result": "failed",
        "severity": "medium",
        "summary": "Lint check failed.",
        "analyzed_at": "2024-01-01T09:00:00",
    },
]

SAMPLE_STATS = {"total": 2, "failed": 2, "succeeded": 0, "critical": 0, "high_severity": 1}


def _make_request(params: dict = None):
    return func.HttpRequest(
        method="GET",
        url="/api/analyses",
        headers={},
        params=params or {},
        body=b"",
    )


class TestIntParam:
    def test_default_returned_when_missing(self):
        req = _make_request()
        assert _int_param(req, "limit", 50) == 50

    def test_valid_int_parsed(self):
        req = _make_request({"limit": "25"})
        assert _int_param(req, "limit", 50) == 25

    def test_max_val_clamped(self):
        req = _make_request({"limit": "9999"})
        assert _int_param(req, "limit", 50, max_val=100) == 100

    def test_negative_clamped_to_zero(self):
        req = _make_request({"offset": "-10"})
        assert _int_param(req, "offset", 0) == 0

    def test_non_numeric_falls_back_to_default(self):
        req = _make_request({"limit": "abc"})
        assert _int_param(req, "limit", 50) == 50


class TestMainHandler:
    @patch("api_get_analyses.cosmos_client.get_analyses", return_value=SAMPLE_ANALYSES)
    @patch("api_get_analyses.cosmos_client.get_stats", return_value=SAMPLE_STATS)
    def test_returns_200_with_correct_shape(self, mock_stats, mock_analyses):
        req = _make_request()
        resp = main(req)

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert "analyses" in body
        assert "stats" in body
        assert "pagination" in body
        assert len(body["analyses"]) == 2

    @patch("api_get_analyses.cosmos_client.get_analyses", return_value=SAMPLE_ANALYSES)
    @patch("api_get_analyses.cosmos_client.get_stats", return_value=SAMPLE_STATS)
    def test_filters_forwarded_to_cosmos(self, mock_stats, mock_analyses):
        req = _make_request({"project": "MyProject", "result": "failed", "severity": "high"})
        main(req)

        mock_analyses.assert_called_once_with(
            limit=50,
            offset=0,
            project_name="MyProject",
            pipeline_name=None,
            result="failed",
            severity="high",
        )

    @patch("api_get_analyses.cosmos_client.get_analyses", return_value=SAMPLE_ANALYSES)
    @patch("api_get_analyses.cosmos_client.get_stats", return_value=SAMPLE_STATS)
    def test_cosmos_internal_fields_stripped(self, mock_stats, mock_analyses):
        dirty = [
            {**SAMPLE_ANALYSES[0], "_rid": "xxx", "_self": "yyy", "_etag": '"zzz"', "_ts": 1234}
        ]
        mock_analyses.return_value = dirty

        req = _make_request()
        resp = main(req)
        body = json.loads(resp.get_body())

        for field in ("_rid", "_self", "_etag", "_ts"):
            assert field not in body["analyses"][0]

    @patch("api_get_analyses.cosmos_client.get_analyses", side_effect=RuntimeError("db down"))
    @patch("api_get_analyses.cosmos_client.get_stats", return_value=SAMPLE_STATS)
    def test_cosmos_error_returns_500(self, mock_stats, mock_analyses):
        req = _make_request()
        resp = main(req)
        assert resp.status_code == 500

    @patch("api_get_analyses.cosmos_client.get_analyses", return_value=SAMPLE_ANALYSES)
    @patch("api_get_analyses.cosmos_client.get_stats", return_value=SAMPLE_STATS)
    def test_cors_header_present(self, mock_stats, mock_analyses):
        req = _make_request()
        resp = main(req)
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"
