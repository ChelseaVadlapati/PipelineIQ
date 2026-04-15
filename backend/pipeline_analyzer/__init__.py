"""
pipeline_analyzer — Cosmos DB change-feed trigger

Fires whenever a new document lands in the `runs` container.
For failed / partially-succeeded runs it fetches Azure DevOps logs,
calls GPT-4o for analysis, and persists an Analysis document.
"""

import asyncio
import logging

import azure.functions as func

from shared.models import Analysis, AnalysisRecommendation
from shared import cosmos_client, devops_client, ai_analyzer

logger = logging.getLogger(__name__)

_ANALYZE_RESULTS = {"failed", "partiallySucceeded"}


async def _analyze_run(run: dict) -> None:
    result = run.get("result", "")
    if result not in _ANALYZE_RESULTS:
        logger.info(
            "Skipping analysis for build %s — result=%s",
            run.get("build_number"), result,
        )
        return

    project = run.get("project_name", "")
    build_id = run.get("build_id", 0)

    logger.info("Analyzing build %s (%s) …", run.get("build_number"), project)

    # Fetch logs and timeline in parallel
    logs, failed_steps = await asyncio.gather(
        devops_client.fetch_build_logs(project, build_id),
        devops_client.fetch_failed_steps(project, build_id),
    )

    ai_result = ai_analyzer.analyze_pipeline_run(
        pipeline_name=run.get("pipeline_name", ""),
        project_name=project,
        build_number=run.get("build_number", ""),
        result=result,
        branch=run.get("source_branch", ""),
        duration_seconds=run.get("duration_seconds") or 0,
        failed_steps=failed_steps,
        logs=logs,
    )

    recommendations = [
        AnalysisRecommendation(**r) if isinstance(r, dict) else r
        for r in ai_result.get("recommendations", [])
    ]

    analysis = Analysis(
        run_id=run["id"],
        build_id=build_id,
        build_number=run.get("build_number", ""),
        pipeline_name=run.get("pipeline_name", ""),
        project_name=project,
        organization=run.get("organization", ""),
        result=result,
        source_branch=run.get("source_branch"),
        duration_seconds=run.get("duration_seconds"),
        summary=ai_result.get("summary", ""),
        root_cause=ai_result.get("root_cause", ""),
        affected_steps=ai_result.get("affected_steps", []),
        error_snippets=ai_result.get("error_snippets", []),
        recommendations=recommendations,
        severity=ai_result.get("severity", "high"),
        confidence=ai_result.get("confidence", 1.0),
    )

    cosmos_client.save_analysis(analysis.model_dump())
    logger.info("Saved analysis %s for run %s", analysis.id, run["id"])


def main(documents: func.DocumentList) -> None:
    if not documents:
        return

    loop = asyncio.new_event_loop()
    try:
        for doc in documents:
            run = dict(doc)
            if run.get("type") != "run":
                continue
            try:
                loop.run_until_complete(_analyze_run(run))
            except Exception as exc:
                logger.exception(
                    "Failed to analyze run %s: %s", run.get("id"), exc
                )
    finally:
        loop.close()
