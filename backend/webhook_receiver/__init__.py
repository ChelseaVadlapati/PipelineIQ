"""
webhook_receiver — HTTP trigger

Receives Azure DevOps build.complete webhook events, validates the shared
secret, persists a PipelineRun document to Cosmos DB, and returns 202.
The Cosmos DB change-feed on the `runs` container automatically triggers
the pipeline_analyzer function.
"""

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone

import azure.functions as func

from shared.models import PipelineRun
from shared import cosmos_client

logger = logging.getLogger(__name__)


def _validate_secret(req: func.HttpRequest) -> bool:
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if not secret:
        return True  # no secret configured — allow all (dev only)
    provided = req.headers.get("X-Pipeline-Secret", "")
    return hmac.compare_digest(secret, provided)


def _parse_run(payload: dict) -> PipelineRun:
    resource = payload.get("resource", {})
    definition = resource.get("definition", {})
    project = resource.get("project", {})
    org_url: str = os.environ.get("AZURE_DEVOPS_ORG_URL", "").rstrip("/")
    org = org_url.split("/")[-1] if org_url else "unknown"

    start_str = resource.get("startTime")
    finish_str = resource.get("finishTime")
    duration_seconds = None
    if start_str and finish_str:
        try:
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            start_dt = datetime.strptime(start_str, fmt).replace(tzinfo=timezone.utc)
            finish_dt = datetime.strptime(finish_str, fmt).replace(tzinfo=timezone.utc)
            duration_seconds = int((finish_dt - start_dt).total_seconds())
        except ValueError:
            pass

    requested_for = (
        resource.get("requestedFor", {}).get("displayName")
        or resource.get("requestedBy", {}).get("displayName")
    )

    return PipelineRun(
        build_id=resource.get("id", 0),
        build_number=resource.get("buildNumber", ""),
        pipeline_name=definition.get("name", "unknown"),
        pipeline_id=definition.get("id", 0),
        project_name=project.get("name", "unknown"),
        project_id=project.get("id", ""),
        organization=org,
        status=resource.get("status", ""),
        result=resource.get("result", ""),
        queue_time=resource.get("queueTime"),
        start_time=start_str,
        finish_time=finish_str,
        duration_seconds=duration_seconds,
        logs_url=resource.get("logs", {}).get("url"),
        build_url=resource.get("url"),
        triggered_by=requested_for,
        source_branch=resource.get("sourceBranch"),
    )


def main(req: func.HttpRequest) -> func.HttpResponse:
    if not _validate_secret(req):
        logger.warning("Webhook received with invalid secret")
        return func.HttpResponse("Unauthorized", status_code=401)

    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)

    event_type = payload.get("eventType", "")
    if event_type != "build.complete":
        return func.HttpResponse(
            json.dumps({"status": "ignored", "eventType": event_type}),
            mimetype="application/json",
            status_code=200,
        )

    try:
        run = _parse_run(payload)
        cosmos_client.save_run(run.model_dump())
        logger.info(
            "Saved run %s — build %s (%s) result=%s",
            run.id, run.build_number, run.pipeline_name, run.result,
        )
        return func.HttpResponse(
            json.dumps({"status": "accepted", "run_id": run.id}),
            mimetype="application/json",
            status_code=202,
        )
    except Exception as exc:
        logger.exception("Error processing webhook: %s", exc)
        return func.HttpResponse("Internal error", status_code=500)
