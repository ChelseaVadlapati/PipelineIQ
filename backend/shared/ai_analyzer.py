import os
import json
import logging
from typing import Dict, Any, List
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert DevOps/platform engineer specializing in CI/CD pipeline diagnostics.
When given a failed or degraded pipeline run, you analyze the logs and timeline to identify
root causes and actionable recommendations.
Always respond with valid JSON only — no markdown fences, no extra text."""

_USER_TEMPLATE = """Analyze this Azure DevOps pipeline run and return a JSON object.

Pipeline:   {pipeline_name}
Project:    {project_name}
Build #:    {build_number}
Result:     {result}
Branch:     {branch}
Duration:   {duration}

Failed / errored steps:
{failed_steps}

Build logs (truncated):
{logs}

Return exactly this JSON structure:
{{
  "summary": "<1-2 sentence plain-English summary of what happened>",
  "root_cause": "<the primary technical root cause>",
  "affected_steps": ["<step name>", ...],
  "error_snippets": ["<key error line 1>", "<key error line 2>", ...],
  "recommendations": [
    {{
      "title": "<short action title>",
      "description": "<detailed description of the fix>",
      "priority": "high|medium|low"
    }}
  ],
  "severity": "critical|high|medium|low|info",
  "confidence": <0.0-1.0>
}}"""


def analyze_pipeline_run(
    pipeline_name: str,
    project_name: str,
    build_number: str,
    result: str,
    branch: str,
    duration_seconds: int,
    failed_steps: List[Dict[str, Any]],
    logs: str,
) -> Dict[str, Any]:
    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version="2024-08-01-preview",
    )
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    steps_text = (
        "\n".join(
            f"  - [{r['result']}] {r['name']} (errors: {r['errorCount']})"
            for r in failed_steps
        )
        or "  (no timeline data available)"
    )

    duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s" if duration_seconds else "unknown"

    user_message = _USER_TEMPLATE.format(
        pipeline_name=pipeline_name,
        project_name=project_name,
        build_number=build_number,
        result=result,
        branch=branch or "unknown",
        duration=duration_str,
        failed_steps=steps_text,
        logs=logs[:12000] if logs else "(no logs available)",
    )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse AI response as JSON: %s", raw[:200])
        return {
            "summary": "Analysis could not be parsed.",
            "root_cause": "Unknown",
            "affected_steps": [],
            "error_snippets": [],
            "recommendations": [],
            "severity": "high",
            "confidence": 0.0,
        }
