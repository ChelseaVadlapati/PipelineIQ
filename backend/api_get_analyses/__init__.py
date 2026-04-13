"""
api_get_analyses — HTTP trigger

GET /api/analyses

Query params:
  limit        int   (default 50, max 100)
  offset       int   (default 0)
  project      str   filter by project_name
  pipeline     str   filter by pipeline_name
  result       str   filter by result (failed | succeeded | partiallySucceeded | canceled)
  severity     str   filter by severity (critical | high | medium | low | info)

Returns paginated analyses + aggregate stats.
"""

import json
import logging

import azure.functions as func

from shared import cosmos_client

logger = logging.getLogger(__name__)


def _int_param(req: func.HttpRequest, name: str, default: int, max_val: int = None) -> int:
    raw = req.params.get(name)
    if raw is None:
        return default
    try:
        val = int(raw)
        if max_val is not None:
            val = min(val, max_val)
        return max(0, val)
    except ValueError:
        return default


def main(req: func.HttpRequest) -> func.HttpResponse:
    limit = _int_param(req, "limit", 50, 100)
    offset = _int_param(req, "offset", 0)
    project = req.params.get("project") or None
    pipeline = req.params.get("pipeline") or None
    result = req.params.get("result") or None
    severity = req.params.get("severity") or None

    try:
        analyses = cosmos_client.get_analyses(
            limit=limit,
            offset=offset,
            project_name=project,
            pipeline_name=pipeline,
            result=result,
            severity=severity,
        )
        stats = cosmos_client.get_stats()
    except Exception as exc:
        logger.exception("Error fetching analyses: %s", exc)
        return func.HttpResponse("Internal error", status_code=500)

    # Strip Cosmos internal fields
    for a in analyses:
        for field in ("_rid", "_self", "_etag", "_attachments", "_ts"):
            a.pop(field, None)

    payload = {
        "analyses": analyses,
        "stats": stats,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "returned": len(analyses),
        },
    }

    return func.HttpResponse(
        json.dumps(payload),
        mimetype="application/json",
        status_code=200,
        headers={"Access-Control-Allow-Origin": "*"},
    )
