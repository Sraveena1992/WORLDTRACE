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


def make_followup_plan(goal, tasks):
    """A SECOND REAL MODEL CALL after observing actual fixture-tool results.

    The model may finish, or request at most three previously unexecuted tools.
    Unsafe or malformed output fails explicitly; no silent local fallback.
    """
    if not configured():
        raise ModelUnavailable("Meta model unavailable for follow-up reasoning")
    executed = [task["tool"] for task in tasks]
    remaining = followup_candidates(executed)
    if not remaining:
        return {"finish": True, "reason": "All approved tools already executed", "steps": [], "tasks": [], "mode": "policy-stop"}
    base = os.environ["WORLDTRACE_MODEL_BASE_URL"].rstrip("/")
    if not base.startswith("https://"):
        raise ModelUnavailable("HTTPS inference endpoint required")
    name = os.getenv("WORLDTRACE_MODEL_NAME", "meta-models/muse-spark-open-1026")
    evidence = [{"tool":t["tool"], "status":t["status"], "result":t.get("result",{})} for t in tasks]
    system = ("You are WORLDTRACE follow-up planner. Review real SYNTHETIC fixture observations. "
              "Return ONLY JSON: either {\\\"finish\\\":true,\\\"reason\\\":\\\"...\\\"} or "
              "{\\\"finish\\\":false,\\\"reason\\\":\\\"...\\\",\\\"steps\\\":[{\\\"id\\\":\\\"...\\\",\\\"tool\\\":\\\"...\\\",\\\"depends_on\\\":[],\\\"objective\\\":\\\"...\\\"}]}. "
              "Choose 1-3 previously UNUSED tools from the provided allowlist only if they add valuable evidence. "
              "Never claim external actions or fixes. Only inspect local synthetic fixtures. No arbitrary code.")
    payload = {"model": name, "messages":[{"role":"system","content":system},
               {"role":"user","content":json.dumps({"goal":goal,"observations":evidence,"remaining_tools":remaining})}],
               "temperature":0.1,"max_tokens":850}
    try:
        with httpx.Client(timeout=45) as client:
            response=client.post(base+"/chat/completions",json=payload,
                 headers={"Authorization":"Bearer "+os.environ["WORLDTRACE_MODEL_API_KEY"]})
            response.raise_for_status()
            data=response.json()
        plan=validate_followup(_decode(data["choices"][0]["message"]["content"]),executed)
        return {"mode":"meta-model-followup","model":data.get("model",name),
                "provider_response_id":data.get("id",""), **plan}
    except (httpx.HTTPError, KeyError, ValueError, TypeError, InvalidPlan) as exc:
        raise ModelUnavailable("Adaptive model follow-up failed: "+str(exc)[:300]) from exc

def probe_provider():
    """Explicit one-shot REAL inference probe. Never sends mission data or secrets in output."""
    if not configured():
        raise ModelUnavailable("Provider URL and API key are not configured")
    base=os.getenv("WORLDTRACE_MODEL_BASE_URL","").rstrip("/")
    if not base.startswith("https://"):
        raise ModelUnavailable("HTTPS inference endpoint required")
    name=os.getenv("WORLDTRACE_MODEL_NAME","meta-models/muse-spark-open-1026")
    payload={"model":name,
             "messages":[{"role":"system","content":"Return the word READY only."},
                         {"role":"user","content":"Connectivity check. Reply READY."}],
             "max_tokens":24,"temperature":0}
    try:
        with httpx.Client(timeout=20) as client:
            response=client.post(base+"/chat/completions",json=payload,
                headers={"Authorization":"Bearer "+os.environ["WORLDTRACE_MODEL_API_KEY"]})
            response.raise_for_status()
            data=response.json()
        output=data["choices"][0]["message"]["content"]
        if not isinstance(output,(str,list)) or not output:
            raise ValueError("Empty model response")
        return {"connected":True,"inference_verified":True,
                "requested_model":name,"returned_model":data.get("model",name),
                "provider":os.getenv("WORLDTRACE_MODEL_PROVIDER","configured endpoint"),
                "response_id":data.get("id",""),
                "message":"Actual inference response received; this does not validate mission planning"}
    except httpx.HTTPStatusError as exc:
        status=exc.response.status_code
        raise ModelUnavailable("Provider rejected inference request (HTTP "+str(status)+"). Check credits, key and model access.") from exc
    except (httpx.HTTPError,KeyError,ValueError,TypeError) as exc:
        raise ModelUnavailable("Model inference probe failed; connection not verified: "+type(exc).__name__) from exc

def make_uploaded_file_plan(goal, roles):
    """REAL model planning over role names only; never upload raw files or excerpts."""
    if not configured():
        raise ModelUnavailable("Meta-compatible inference is not configured")
    roles=list(roles)
    if not roles or len(set(roles))!=len(roles):
        raise ModelUnavailable("Invalid file-role inventory")
    base=os.environ["WORLDTRACE_MODEL_BASE_URL"].rstrip("/")
    if not base.startswith("https://"):raise ModelUnavailable("HTTPS inference endpoint required")
    name=os.getenv("WORLDTRACE_MODEL_NAME","meta-models/muse-spark-open-1026")
    system=("You are WORLDTRACE Mission Commander. Output ONLY valid JSON: "
            '{"ordered_roles":["role1","role2"],"reason":"short rationale"}. '
            "The list MUST include EACH supplied role EXACTLY ONCE. "
            "You may reorder but may not add, drop, duplicate, rename or invent roles. "
            "There are no external write permissions. Only validated local parsers execute. "
            "Do not claim actual resolution, successful execution or independent verification.")
    payload={"model":name,"messages":[{"role":"system","content":system},
       {"role":"user","content":json.dumps({"goal":goal,"available_file_roles":roles})}],
       "max_tokens":400,"temperature":0}
    try:
        with httpx.Client(timeout=35) as client:
            response=client.post(base+"/chat/completions",json=payload,
                headers={"Authorization":"Bearer "+os.environ["WORLDTRACE_MODEL_API_KEY"]})
            response.raise_for_status()
            data=response.json()
        parsed=_decode(data["choices"][0]["message"]["content"])
        ordered=parsed.get("ordered_roles")
        reason=parsed.get("reason")
        if not isinstance(ordered,list) or any(not isinstance(r,str) for r in ordered) or sorted(ordered)!=sorted(roles):
            raise ValueError("Model plan did not cover the exact input roles")
        if not isinstance(reason,str) or not reason.strip():
            raise ValueError("Model plan missing a rationale")
        return {"ordered_roles":ordered,"reason":reason[:450],
                "requested_model":name,"model":data.get("model",name),
                "provider_response_id":data.get("id",""),
                "provider":os.getenv("WORLDTRACE_MODEL_PROVIDER","configured endpoint")}
    except httpx.HTTPStatusError as exc:
        raise ModelUnavailable("Meta model planning provider rejected request (HTTP "+
             str(exc.response.status_code)+"). Check activated credits and model access.") from exc
    except (httpx.HTTPError,KeyError,ValueError,TypeError,AttributeError) as exc:
        raise ModelUnavailable("Meta model file planning unavailable: "+type(exc).__name__) from exc

def assess_uploaded_evidence(goal, observations, cross_checks):
    """Second genuine model call, after tools, with coarse sanitized findings only.

    The model returns non-executable hypotheses. Host validates each evidence
    reference and refuses extra/unrecognized input roles.
    """
    if not configured():
        raise ModelUnavailable("Meta-compatible inference is not configured")
    base=os.environ["WORLDTRACE_MODEL_BASE_URL"].rstrip("/")
    if not base.startswith("https://"):
        raise ModelUnavailable("HTTPS inference endpoint required")
    name=os.getenv("WORLDTRACE_MODEL_NAME","meta-models/muse-spark-open-1026")
    evidence=[]
    for item in observations:
        result=item["result"]
        counts={}
        for key in ("pages","characters","source_rows","target_rows","failure_count",
                    "total_requests","messages","records","expected_status","simulated_status"):
            if type(result.get(key)) is int:
                counts[key]=result[key]
        for key in ("missing_ids","extra_ids","mismatched_ids","duplicates","invalid_lines"):
            if isinstance(result.get(key),list):
                counts[key+"_count"]=len(result[key])
        evidence.append({"role":item["role"],"tool":item["tool"],
                         "status":item["status"],"metrics":counts})
    role_ids={x["role"] for x in observations}
    checks=[{"name":c["name"],"matched":c["matched"]} for c in cross_checks]
    prompt=("You are a cautious operational incident analyst. "
            "Return JSON ONLY, fields: summary (string), "
            "hypotheses (1-3 items, each claim string, evidence_roles array, "
            "confidence low/medium/high), next_action (string). "
            "Use ONLY the observed counts and checks, no fabricated facts or claims "
            "of executed repairs. Never propose an external side effect as completed. "
            "Explicitly distinguish hypotheses from proven observations.")
    payload={"model":name,"messages":[{"role":"system","content":prompt},
          {"role":"user","content":json.dumps({"instruction":goal,"evidence":evidence,
                                               "cross_checks":checks})}],
          "max_tokens":900,"temperature":0.1}
    try:
        with httpx.Client(timeout=45) as client:
            response=client.post(base+"/chat/completions",json=payload,
              headers={"Authorization":"Bearer "+os.environ["WORLDTRACE_MODEL_API_KEY"]})
            response.raise_for_status()
            data=response.json()
        parsed=_decode(data["choices"][0]["message"]["content"])
        if not isinstance(parsed,dict):
            raise ValueError("Invalid analysis object")
        summary=parsed.get("summary");next_action=parsed.get("next_action")
        hypotheses=parsed.get("hypotheses")
        if not isinstance(summary,str) or not summary.strip() or len(summary)>1000:
            raise ValueError("Invalid summary")
        if not isinstance(next_action,str) or not next_action.strip() or len(next_action)>1000:
            raise ValueError("Invalid next action")
        if not isinstance(hypotheses,list) or not 1<=len(hypotheses)<=3:
            raise ValueError("Invalid hypotheses")
        validated=[]
        for h in hypotheses:
            if not isinstance(h,dict):
                raise ValueError("Invalid hypothesis")
            claim=h.get("claim");refs=h.get("evidence_roles");confidence=h.get("confidence")
            if (not isinstance(claim,str) or not claim.strip() or len(claim)>600
                or not isinstance(refs,list) or not refs
                or any(not isinstance(ref,str) for ref in refs)
                or not set(refs).issubset(role_ids)
                or confidence not in ("low","medium","high")):
                raise ValueError("Unverifiable hypothesis or unsupported evidence reference")
            validated.append({"claim":claim,"evidence_roles":list(dict.fromkeys(refs)),
                              "confidence":confidence})
        return {"summary":summary,"hypotheses":validated,"next_action":next_action,
                "model":data.get("model",name),"provider_response_id":data.get("id",""),
                "scope":"Advisory hypotheses, no autonomous external action",
                "provided_evidence":"Sanitized role IDs, statuses, and counts only"}
    except httpx.HTTPStatusError as exc:
        raise ModelUnavailable("Model evidence reasoning rejected request (HTTP "+
            str(exc.response.status_code)+"). Check key, credits and access.") from exc
    except (httpx.HTTPError,KeyError,ValueError,TypeError,AttributeError) as exc:
        raise ModelUnavailable("Meta evidence reasoning unavailable: "+type(exc).__name__) from exc
