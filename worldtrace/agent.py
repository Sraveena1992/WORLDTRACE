"""WORLDTRACE model planner; a configured endpoint is NOT proof of successful inference."""
import json
import os
import httpx
from .planning import validate_plan, InvalidPlan
from .local_routing import select_local_tools

DEFAULT_TOOLS = ["pdf_inspect","email_inspect","network_inspect","etl_compare","database_check","api_virtualize","performance_probe","middleware_test","mainframe_contract"]

class ModelUnavailable(RuntimeError):
    pass

def configured():
    return bool(os.getenv("WORLDTRACE_MODEL_BASE_URL") and os.getenv("WORLDTRACE_MODEL_API_KEY"))

def _decode(raw):
    if isinstance(raw, list):
        raw = "".join(item.get("text", "") for item in raw if isinstance(item, dict))
    if not isinstance(raw, str):
        raise ValueError("Model returned no text")
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            raw = "\n".join(lines[1:-1]).strip()
    return json.loads(raw)

def make_plan(goal, use_model):
    if not use_model:
        selected, reason = select_local_tools(goal)
        return {"mode": "local-workflow", **validate_plan({"reason": reason, "tasks": selected})}
    if not configured():
        raise ModelUnavailable("Meta inference is not configured. Set a verified HTTPS provider and key.")
    base = os.environ["WORLDTRACE_MODEL_BASE_URL"].rstrip("/")
    if not base.startswith("https://"):
        raise ModelUnavailable("HTTPS inference endpoint required")
    key = os.environ["WORLDTRACE_MODEL_API_KEY"]
    name = os.getenv("WORLDTRACE_MODEL_NAME", "meta-models/muse-spark-open-1026")
    from .tools import AVAILABLE
    system = ("You are WORLDTRACE Mission Commander. Output ONLY a JSON object with reason and steps. "
              "Every step must include id, tool, depends_on (array of step IDs) and objective. "
              "Choose 2-9 distinct relevant tools from supplied allowlist, making an acyclic dependency graph. "
              "Tools inspect SYNTHETIC LOCAL fixtures only, not real external systems. "
              "Do not claim any actual repair, approval, email sent, physical-world proof or execution success. "
              "All returned steps will be validated by the host before execution.")
    payload = {"model": name, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps({"mission": goal, "available_tools": sorted(AVAILABLE)})}
    ], "temperature": 0.15, "max_tokens": 1300}
    try:
        with httpx.Client(timeout=45) as client:
            response = client.post(base + "/chat/completions", json=payload, headers={"Authorization": f"Bearer {key}"})
            response.raise_for_status()
            response_data = response.json()
        plan = validate_plan(_decode(response_data["choices"][0]["message"]["content"]))
        return {"mode": "meta-model", "model": response_data.get("model", name),
                "requested_model": name,
                "provider": os.getenv("WORLDTRACE_MODEL_PROVIDER", "configured endpoint"),
                "provider_response_id": response_data.get("id", ""), **plan}
    except (httpx.HTTPError, KeyError, ValueError, TypeError, InvalidPlan) as exc:
        raise ModelUnavailable("Model planning failed: " + str(exc)[:300]) from exc
