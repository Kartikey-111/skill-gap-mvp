# main.py - Minimal SKILL Gap MVP (FastAPI) with CORS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import time, uuid, datetime

app = FastAPI(title="SKILL Gap MVP")

# ------------------- CORS Middleware -------------------
# Allow requests from any origin (frontend / browser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- Pydantic Models -------------------
class ResponseItem(BaseModel):
    item_id: str
    type: str
    answer: Any
    correct: Optional[Any] = None
    time_sec: Optional[float] = None
    skill_refs: Optional[List[str]] = None
    score_rubric: Optional[dict] = None

class Payload(BaseModel):
    schema_version: str
    assessment_id: str
    student_id: str
    locale: Optional[str] = None
    responses: List[ResponseItem]
    timestamp: Optional[str] = None
    constraints: Optional[dict] = None
    options: Optional[dict] = None
    student_profile: Optional[dict] = None
    context: Optional[dict] = None

# ------------------- Health Check -------------------
@app.get("/health")
def health():
    return {"status":"ok"}

# ------------------- Credit Computation -------------------
def compute_credit(it: ResponseItem) -> float:
    t = (it.type or "").lower()
    # MCQ exact match
    if t == "mcq":
        return 1.0 if it.answer == it.correct else 0.0
    # MSQ: fraction of correct choices selected
    if t == "msq":
        try:
            ans = set(it.answer or [])
            corr = set(it.correct or [])
            if not corr:
                return 0.0
            return len(ans & corr) / len(corr)
        except Exception:
            return 0.0
    # Numeric within tolerance
    if t == "numeric":
        try:
            return 1.0 if abs(float(it.answer) - float(it.correct)) <= 1e-3 else 0.0
        except Exception:
            return 0.0
    # Short/Long text: simple substring baseline
    if t in ("short", "long"):
        try:
            return 1.0 if str(it.correct).lower() in str(it.answer).lower() else 0.0
        except Exception:
            return 0.0
    # default
    return 0.0

# ------------------- Diagnostics Endpoint -------------------
@app.post("/diagnostics/generate")
def generate(payload: Payload):
    start = time.time()
    # aggregate per-skill statistics
    skills = {}
    for it in payload.responses:
        credit = compute_credit(it)
        refs = it.skill_refs or []
        for k in refs:
            rec = skills.setdefault(k, {"correct": 0.0, "total": 0})
            rec["total"] += 1
            rec["correct"] += float(credit)

    # Beta-Binomial posterior mean with alpha=1,beta=1
    alpha = 1.0
    beta = 1.0
    mastery_vector = []
    for k, rec in skills.items():
        c = rec["correct"]
        n = rec["total"]
        mean = (c + alpha) / (n + alpha + beta) if n >= 0 else alpha / (alpha + beta)
        var = ((c + alpha) * (n - c + beta)) / (((n + alpha + beta) ** 2) * (n + alpha + beta + 1)) if n > 0 else 0.0
        mastery_vector.append({"skill_id": k, "score": round(mean, 3), "uncertainty": round(var, 6)})

    # gaps by thresholds
    gaps = []
    for m in mastery_vector:
        s = m["score"]
        if s < 0.5:
            sev = "high"
        elif s < 0.75:
            sev = "med"
        elif s < 0.85:
            sev = "low"
        else:
            continue
        gaps.append({"skill_id": m["skill_id"], "severity": sev})

    # curriculum: top-k lowest mastery
    max_acts = 5
    if payload.options and isinstance(payload.options, dict):
        max_acts = int(payload.options.get("max_activities", max_acts))
    mastery_sorted = sorted(mastery_vector, key=lambda x: x["score"])
    objectives = []
    activities = []
    for i, m in enumerate(mastery_sorted[:max_acts]):
        obj_id = f"o{i+1}"
        target = min(0.85, m["score"] + 0.2)
        objectives.append({"id": obj_id, "skill_id": m["skill_id"], "target_score": round(target, 3)})
        activities.append({"id": f"a{i+1}", "label": f"Practice: {m['skill_id']}", "estimated_minutes": 30, "skill_refs": [m["skill_id"]]})

    # naive prediction: average mastery
    avg = sum([m["score"] for m in mastery_vector]) / len(mastery_vector) if mastery_vector else 0.0
    prob_pass = round(avg, 3)
    if prob_pass >= 0.85:
        band = "A"
    elif prob_pass >= 0.7:
        band = "B"
    elif prob_pass >= 0.5:
        band = "C"
    else:
        band = "D"

    avg_uncertainty = sum([m["uncertainty"] for m in mastery_vector]) / len(mastery_vector) if mastery_vector else 0.0
    confidence_score = round(max(0.0, min(1.0, 1.0 - avg_uncertainty)), 3)
    processing_ms = int((time.time() - start) * 1000)

    result = {
        "primary_id": str(uuid.uuid4()),
        "main_response": {
            "content": {
                "mastery_vector": mastery_vector,
                "gaps": gaps,
                "curriculum_plan": {
                    "objectives": objectives,
                    "activities": activities,
                    "rationale": "Baseline: address lowest mastery skills first; conservative targets."
                },
                "predictions": [{"subject": "general", "horizon_days": 30, "prob_pass": prob_pass, "band": band}]
            },
            "metadata": [{"key": "alignment_version", "value": "v1"}],
            "confidence_score": confidence_score,
            "uncertainty_factors": []
        },
        "supporting_data": [],
        "performance_metrics": {"latency_ms": processing_ms, "processing_ms": processing_ms, "cost_units": 0.0},
        "system_metadata": {"model_info": "baseline-beta-binomial", "strategy_info": "mvp", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}
    }
    return result
