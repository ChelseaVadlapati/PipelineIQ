"""
Tests for webhook_receiver — payload parsing and secret validation.
"""

import json
import pytest
import azure.functions as func

from webhook_receiver import _parse_run, _validate_secret, main


class FakeRequest:
    """Minimal HttpRequest stand-in for testing."""

    def __init__(self, body: dict, headers: dict = None):
        self._body = json.dumps(body).encode()
        self.headers = headers or {}
        self.route_params = {}

    def get_json(self):
        return json.loads(self._body)


# ── _parse_run ────────────────────────────────────────────────────────────────

class TestParseRun:
    def test_basic_fields(self, ado_build_complete_payload):
        run = _parse_run(ado_build_complete_payload)
        assert run.build_id == 9001
        assert run.build_number == "20240101.5"
        assert run.pipeline_name == "backend-ci"
        assert run.pipeline_id == 7
        assert run.project_name == "MyProject"
        assert run.project_id == "proj-uuid-001"
        assert run.result == "failed"
        assert run.status == "completed"

    def test_organization_extracted_from_org_url(self, ado_build_complete_payload):
        run = _parse_run(ado_build_complete_payload)
        assert run.organization == "test-org"

    def test_duration_calculated(self, ado_build_complete_payload):
        run = _parse_run(ado_build_complete_payload)
        # 09:01:00 → 09:05:30 = 270 seconds
        assert run.duration_seconds == 270

    def test_source_branch(self, ado_build_complete_payload):
        run = _parse_run(ado_build_complete_payload)
        assert run.source_branch == "refs/heads/main"

    def test_triggered_by(self, ado_build_complete_payload):
        run = _parse_run(ado_build_complete_payload)
        assert run.triggered_by == "Alice Smith"

    def test_logs_url(self, ado_build_complete_payload):
        run = _parse_run(ado_build_complete_payload)
        assert run.logs_url is not None
        assert "9001/logs" in run.logs_url

    def test_run_type_field(self, ado_build_complete_payload):
        run = _parse_run(ado_build_complete_payload)
        assert run.type == "run"

    def test_id_is_generated(self, ado_build_complete_payload):
        run1 = _parse_run(ado_build_complete_payload)
        run2 = _parse_run(ado_build_complete_payload)
        # Each call generates a new UUID
        assert run1.id != run2.id

    def test_duration_none_if_times_missing(self, ado_build_complete_payload):
        payload = ado_build_complete_payload.copy()
        payload["resource"] = {**payload["resource"], "startTime": None, "finishTime": None}
        run = _parse_run(payload)
        assert run.duration_seconds is None

    def test_missing_optional_fields(self):
        minimal = {
            "resource": {
                "id": 1,
                "buildNumber": "1.0",
                "status": "completed",
                "result": "failed",
                "definition": {"id": 1, "name": "pipeline"},
                "project": {"id": "p1", "name": "proj"},
            }
        }
        run = _parse_run(minimal)
        assert run.build_id == 1
        assert run.source_branch is None
        assert run.triggered_by is None


# ── _validate_secret ──────────────────────────────────────────────────────────

class TestValidateSecret:
    def test_valid_secret_accepted(self):
        req = FakeRequest({}, headers={"X-Pipeline-Secret": "super-secret"})
        assert _validate_secret(req) is True

    def test_invalid_secret_rejected(self):
        req = FakeRequest({}, headers={"X-Pipeline-Secret": "wrong-secret"})
        assert _validate_secret(req) is False

    def test_missing_header_rejected(self):
        req = FakeRequest({}, headers={})
        assert _validate_secret(req) is False

    def test_no_configured_secret_allows_all(self, monkeypatch):
        monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
        req = FakeRequest({}, headers={})
        assert _validate_secret(req) is True


# ── main handler ──────────────────────────────────────────────────────────────

class TestMainHandler:
    def test_wrong_secret_returns_401(self):
        req = FakeRequest(
            {"eventType": "build.complete"},
            headers={"X-Pipeline-Secret": "bad"},
        )
        resp = main(req)
        assert resp.status_code == 401

    def test_invalid_json_returns_400(self):
        req = func.HttpRequest(
            method="POST",
            url="/api/webhook",
            headers={"X-Pipeline-Secret": "super-secret"},
            body=b"not json",
        )
        resp = main(req)
        assert resp.status_code == 400

    def test_non_build_event_returns_200_ignored(self, mocker):
        mocker.patch("webhook_receiver.cosmos_client.save_run")
        req = FakeRequest(
            {"eventType": "git.push"},
            headers={"X-Pipeline-Secret": "super-secret"},
        )
        resp = main(req)
        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["status"] == "ignored"

    def test_valid_payload_returns_202(self, mocker, ado_build_complete_payload):
        mocker.patch("webhook_receiver.cosmos_client.save_run", return_value={})
        req = FakeRequest(
            ado_build_complete_payload,
            headers={"X-Pipeline-Secret": "super-secret"},
        )
        resp = main(req)
        assert resp.status_code == 202
        body = json.loads(resp.get_body())
        assert body["status"] == "accepted"
        assert "run_id" in body
