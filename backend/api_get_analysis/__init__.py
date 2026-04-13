"""
api_get_analysis — HTTP trigger

GET /api/analyses/{analysis_id}

Returns a single Analysis document from Cosmos DB.
"""

import json
import logging

import azure.functions as func

from shared import cosmos_client

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    analysis_id = req.route_params.get("analysis_id")
    if not analysis_id:
        return func.HttpResponse(
            json.dumps({"error": "analysis_id is required"}),
            mimetype="application/json",
            status_code=400,
        )

    analysis = cosmos_client.get_analysis(analysis_id)
    if analysis is None:
        return func.HttpResponse(
            json.dumps({"error": "Analysis not found"}),
            mimetype="application/json",
            status_code=404,
        )

    # Remove Cosmos DB internal fields
    analysis.pop("_rid", None)
    analysis.pop("_self", None)
    analysis.pop("_etag", None)
    analysis.pop("_attachments", None)
    analysis.pop("_ts", None)

    return func.HttpResponse(
        json.dumps(analysis),
        mimetype="application/json",
        status_code=200,
        headers={"Access-Control-Allow-Origin": "*"},
    )
