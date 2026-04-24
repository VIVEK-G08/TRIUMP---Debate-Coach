from constants import COACH_NAME, INTENSITY_TONE


def build_debate_prompt(argument, mode, eff, profile, debate_style, topic):
    tone_lvl = max(1, min(5, round(eff)))
    tone = INTENSITY_TONE[tone_lvl]
    profile_ctx = ""
    if profile and isinstance(profile, dict) and "argument_style" in profile:
        profile_ctx = f"""
Known debater profile (personalise critique using this):
  Style:             {profile.get('argument_style','—')}
  Dominant weakness: {profile.get('dominant_fallacy','—')}
  Predicted failure: {profile.get('predicted_weakness','—')}
"""
    mode_instr = {
      "debate":    "Accept the argument clearly. Then provide a strong counterargument, list logical flaws, analyze factual claims, and give practical improvement tips for a learner.",
      "critique":  "Accept the argument clearly. Then critique its strengths and weaknesses, expose every flaw, analyze factual claims, and give clear improvement advice.",
      "factcheck": "Extract every factual claim. Assess each as supported, contested, or unsupported. Also generate balanced support and counter evidence."
    }.get(mode, "")

    style_ctx = f"Preferred voice: {debate_style}."
    topic_ctx = f"Topic: {topic}." if topic and topic != "General" else ""
    return f'''You are {COACH_NAME}, a constructive debate coach who teaches beginners how to improve.
Tone: {tone}. {style_ctx}
{profile_ctx}
{topic_ctx}
Argument:
"{argument}"

Task: {mode_instr}

The user is learning debate skills. Keep feedback clear, detailed, and encouraging. Reward reasonable reasoning and give concrete next steps to improve.

Requirements for evidence quality:
1) Produce at least 6 fact-based statements that SUPPORT the user's argument.
2) Produce at least 6 fact-based statements that COUNTER the user's argument.
3) Each fact item must include a clear claim, verdict, and concise rationale.
4) If the argument is generalized or vague, infer reasonable context and assumptions; do not fail.
5) Rephrase the original argument into a stronger, more precise version while preserving user intent.
6) Keep output practical for deciding whether the argument is strong or weak based on evidence.

CRITICAL: Respond ONLY with valid JSON. No text outside the JSON block.
{{
  "summary":          "One-sentence summary of the argument",
  "reframed_argument": "A stronger, more precise version of the user's argument",
  "counterargument":  "rebuttal string or empty string for critique/factcheck",
  "flaws":            ["flaw 1", "flaw 2", "flaw 3"],
  "facts":            [
    {{"stance":"support", "claim":"...", "verdict":"supported|contested|unsupported", "note":"...", "source_hint":"..."}},
    {{"stance":"counter", "claim":"...", "verdict":"supported|contested|unsupported", "note":"...", "source_hint":"..."}}
  ],
  "strength_score":   1-10,
  "strength_label":   "weak|moderate|strong|very strong",
  "fallacy_count":    0,
  "fallacy_types":    ["fallacy name"],
  "improvement_tips": ["..."],
  "learning_summary": "One sentence on what to learn next",
  "session_tag":      "3-5 word behavioral summary"
}}'''
