from constants import INTENSITY_TONE
from groq_api import call_groq_llm, extract_json


def compute_effective_intensity(base, sessions):
    if not sessions:
        return float(base)
    recent5 = sessions[:5]
    avg_f = sum(s["fallacy_count"] for s in recent5) / len(recent5)
    fallacy_rate = min(avg_f / 5.0, 1.0)
    recent3 = [s["strength_score"] for s in sessions[:3] if s["strength_score"]]
    if len(recent3) >= 2:
        delta = recent3[0] - recent3[-1]
        improvement_trend = max(-1.0, min(1.0, delta / 10.0))
    else:
        improvement_trend = 0.0
    raw = base * (1 + fallacy_rate) * (1 - improvement_trend * 0.3)
    return round(max(1.0, min(5.0, raw)), 2)


def intensity_breakdown(base, sessions):
    recent5 = sessions[:5] if sessions else []
    avg_f = sum(s["fallacy_count"] for s in recent5) / max(len(recent5), 1) if recent5 else 0
    fr = round(min(avg_f / 5.0, 1.0), 3)
    recent3 = [s["strength_score"] for s in sessions[:3] if s["strength_score"]] if sessions else []
    if len(recent3) >= 2:
        delta = recent3[0] - recent3[-1]
        it = round(max(-1.0, min(1.0, delta / 10.0)), 3)
    else:
        it = 0.0
    eff = round(max(1.0, min(5.0, base * (1 + fr) * (1 - it * 0.3))), 2)
    return {"fallacy_rate": fr, "improvement_trend": it, "effective": eff}


def build_behaviour_profile(sessions, api_key):
    if len(sessions) < 3 or not api_key:
        return None
    history = "\\n".join([
        f"[{i+1}] score={s['strength_score']}/10  fallacies={s['fallacy_count']}  "
        f"types={s['fallacy_types']}  tag={s['session_tag']}"
        for i, s in enumerate(sessions[:8])
    ])
    prompt = f"""You are a debate coach analyzing a student's argument patterns.
Sessions (most recent first):
{history}

Output ONLY valid JSON, nothing else:
{{
  "dominant_fallacy":   "most repeated fallacy or none detected",
  "argument_style":     "one concise phrase",
  "trend":              "improving|declining|inconsistent|stable",
  "predicted_weakness": "what will likely fail in their next argument",
  "coaching_tip":       "one specific actionable tip under 20 words",
  "avg_score":          0.0
}}"""
    raw = call_groq_llm(prompt, api_key)
    return extract_json(raw)
