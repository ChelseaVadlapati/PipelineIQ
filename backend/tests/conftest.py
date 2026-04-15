"""
Shared fixtures for all backend tests.
"""

import pytest


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    """Inject required environment variables for every test."""
    monkeypatch.setenv("AZURE_DEVOPS_ORG_URL", "https://dev.azure.com/test-org")
    monkeypatch.setenv("AZURE_DEVOPS_PAT", "test-pat")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://test.documents.azure.com:443/")
    monkeypatch.setenv("COSMOS_KEY", "test-cosmos-key==")
    monkeypatch.setenv("COSMOS_DB", "pipelineiq")
    monkeypatch.setenv("COSMOS_CONTAINER", "analyses")
    monkeypatch.setenv("WEBHOOK_SECRET", "super-secret")


# ── Sample Azure DevOps build.complete payload ────────────────────────────────

@pytest.fixture
def ado_build_complete_payload():
    return {
        "subscriptionId": "aaaaaaaa-0000-0000-0000-000000000001",
        "notificationId": 42,
        "id": "event-id-001",
        "eventType": "build.complete",
        "publisherId": "tfs",
        "resource": {
            "id": 9001,
            "buildNumber": "20240101.5",
            "status": "completed",
            "result": "failed",
            "queueTime": "2024-01-01T09:00:00.000Z",
            "startTime": "2024-01-01T09:01:00.000Z",
            "finishTime": "2024-01-01T09:05:30.000Z",
            "url": "https://dev.azure.com/test-org/MyProject/_apis/build/builds/9001",
            "definition": {
                "id": 7,
                "name": "backend-ci",
                "url": "https://dev.azure.com/test-org/MyProject/_apis/build/definitions/7",
            },
            "project": {
                "id": "proj-uuid-001",
                "name": "MyProject",
            },
            "logs": {
                "id": 0,
                "type": "container",
                "url": "https://dev.azure.com/test-org/MyProject/_apis/build/builds/9001/logs",
            },
            "sourceBranch": "refs/heads/main",
            "requestedFor": {"displayName": "Alice Smith"},
        },
    }


@pytest.fixture
def ado_build_succeeded_payload(ado_build_complete_payload):
    payload = ado_build_complete_payload.copy()
    payload["resource"] = {**payload["resource"], "result": "succeeded"}
    return payload
