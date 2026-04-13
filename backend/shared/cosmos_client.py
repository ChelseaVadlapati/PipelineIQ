import os
import logging
from azure.cosmos import CosmosClient, exceptions
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

_RUNS_CONTAINER = "runs"


def _get_container(container_name: str):
    endpoint = os.environ["COSMOS_ENDPOINT"]
    key = os.environ["COSMOS_KEY"]
    db_name = os.environ.get("COSMOS_DB", "pipelineiq")
    client = CosmosClient(endpoint, key)
    db = client.get_database_client(db_name)
    return db.get_container_client(container_name)


def _analyses_container():
    return _get_container(os.environ.get("COSMOS_CONTAINER", "analyses"))


def save_run(run_dict: dict) -> dict:
    return _get_container(_RUNS_CONTAINER).upsert_item(run_dict)


def save_analysis(analysis_dict: dict) -> dict:
    return _analyses_container().upsert_item(analysis_dict)


def get_analysis(analysis_id: str) -> Optional[dict]:
    try:
        return _analyses_container().read_item(
            item=analysis_id, partition_key=analysis_id
        )
    except exceptions.CosmosResourceNotFoundError:
        return None


def get_analyses(
    limit: int = 50,
    offset: int = 0,
    project_name: Optional[str] = None,
    pipeline_name: Optional[str] = None,
    result: Optional[str] = None,
    severity: Optional[str] = None,
) -> List[dict]:
    conditions = ["c.type = 'analysis'"]
    params: List[Dict[str, Any]] = []

    if project_name:
        conditions.append("c.project_name = @project_name")
        params.append({"name": "@project_name", "value": project_name})
    if pipeline_name:
        conditions.append("c.pipeline_name = @pipeline_name")
        params.append({"name": "@pipeline_name", "value": pipeline_name})
    if result:
        conditions.append("c.result = @result")
        params.append({"name": "@result", "value": result})
    if severity:
        conditions.append("c.severity = @severity")
        params.append({"name": "@severity", "value": severity})

    where = " AND ".join(conditions)
    query = (
        f"SELECT * FROM c WHERE {where} "
        f"ORDER BY c.analyzed_at DESC "
        f"OFFSET {offset} LIMIT {limit}"
    )

    return list(
        _analyses_container().query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True,
        )
    )


def get_stats() -> Dict[str, Any]:
    """Return aggregate stats across all analyses."""
    container = _analyses_container()

    def _count(where_extra: str = "") -> int:
        where = "c.type = 'analysis'"
        if where_extra:
            where += f" AND {where_extra}"
        rows = list(container.query_items(
            query=f"SELECT VALUE COUNT(1) FROM c WHERE {where}",
            enable_cross_partition_query=True,
        ))
        return rows[0] if rows else 0

    return {
        "total":         _count(),
        "failed":        _count("c.result = 'failed'"),
        "succeeded":     _count("c.result = 'succeeded'"),
        "critical":      _count("c.severity = 'critical'"),
        "high_severity": _count("c.severity = 'high'"),
    }
