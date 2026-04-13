import os
import base64
import logging
import asyncio
from typing import List, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

_API_VERSION = "7.1"
_MAX_LOG_LINES = 100  # lines per log file kept for analysis
_MAX_LOG_FILES = 8    # last N log files fetched


def _auth_headers() -> dict:
    pat = os.environ["AZURE_DEVOPS_PAT"]
    token = base64.b64encode(f":{pat}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }


def _org_url() -> str:
    return os.environ["AZURE_DEVOPS_ORG_URL"].rstrip("/")


async def fetch_build_logs(project: str, build_id: int) -> str:
    """Fetch and concatenate relevant build logs from Azure DevOps."""
    base = _org_url()
    headers = _auth_headers()
    logs_url = (
        f"{base}/{project}/_apis/build/builds/{build_id}/logs"
        f"?api-version={_API_VERSION}"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(logs_url, headers=headers) as resp:
            if resp.status != 200:
                logger.warning("Could not list logs for build %s: HTTP %s", build_id, resp.status)
                return ""
            data = await resp.json()

        log_entries = data.get("value", [])
        # Fetch the last N log files (most likely to contain errors)
        selected = log_entries[-_MAX_LOG_FILES:]

        async def fetch_one(log_id: int) -> str:
            url = (
                f"{base}/{project}/_apis/build/builds/{build_id}/logs/{log_id}"
                f"?api-version={_API_VERSION}"
            )
            async with session.get(url, headers=headers) as r:
                if r.status != 200:
                    return ""
                text = await r.text()
                lines = text.splitlines()
                if len(lines) > _MAX_LOG_LINES * 2:
                    # Keep first and last segments to capture setup + failure
                    kept = lines[:_MAX_LOG_LINES] + ["... (truncated) ..."] + lines[-_MAX_LOG_LINES:]
                    return "\n".join(kept)
                return text

        tasks = [fetch_one(e["id"]) for e in selected]
        results = await asyncio.gather(*tasks)

    parts = []
    for entry, content in zip(selected, results):
        if content:
            parts.append(f"=== Log {entry['id']} ===\n{content}")

    return "\n\n".join(parts)


async def fetch_failed_steps(project: str, build_id: int) -> List[Dict[str, Any]]:
    """Return a list of failed / errored timeline records for the build."""
    base = _org_url()
    url = (
        f"{base}/{project}/_apis/build/builds/{build_id}/timeline"
        f"?api-version={_API_VERSION}"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_auth_headers()) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()

    records = data.get("records", [])
    return [
        {
            "name": r.get("name"),
            "type": r.get("type"),
            "result": r.get("result"),
            "errorCount": r.get("errorCount", 0),
            "warningCount": r.get("warningCount", 0),
        }
        for r in records
        if r.get("result") in ("failed", "canceled") or r.get("errorCount", 0) > 0
    ]
