from __future__ import annotations

import json

from prompts import build_debate_prompt


def normalized_stance(value):
    # Normalize text so support/counter labels can be compared consistently.
    return str(value or "").strip().lower()


def count_stance(facts, stance):
    # Count facts that match one stance label in the model output.
    target = normalized_stance(stance)
    return sum(1 for fact in facts if isinstance(fact, dict) and normalized_stance(fact.get("stance")) == target)


def fact_counts(facts):
    # Return support/counter counts together because the UI needs both values repeatedly.
    return count_stance(facts, "support"), count_stance(facts, "counter")


def build_repair_prompt(argument, mode, eff, profile, debate_style, topic, previous_result, need_support, need_counter):
    # When the first answer is thin, ask the model to regenerate a fuller evidence-balanced version.
    base_prompt = build_debate_prompt(argument, mode, eff, profile, debate_style, topic)
    return f"""{base_prompt}

Previous model output did not satisfy evidence minimums.
Need at least {need_support} more SUPPORT facts and {need_counter} more COUNTER facts.

Return a full corrected JSON object from scratch.
Keep all previous required keys.
Ensure facts contain a balanced list with at least 6 support and 6 counter items total.

Previous JSON (for reference):
{json.dumps(previous_result, ensure_ascii=True)}
"""


def session_points(result, support_count, counter_count, diagnostics):
    # XP rewards balanced, well-explained answers and penalizes noisy or incomplete outputs.
    score = int(result.get("strength_score", 0) or 0)
    fallacies = int(result.get("fallacy_count", 0) or 0)
    base = 30 + score * 5
    evidence_bonus = min(24, (support_count + counter_count) * 2)
    balance_bonus = 12 if support_count >= 6 and counter_count >= 6 else 0
    clarity_bonus = 8 if result.get("summary") else 0
    reframing_bonus = 10 if result.get("reframed_argument") else 0
    diagnostic_penalty = min(20, len(diagnostics) * 2)
    fallacy_penalty = fallacies * 2
    points = base + evidence_bonus + balance_bonus + clarity_bonus + reframing_bonus - diagnostic_penalty - fallacy_penalty
    return max(10, min(150, points))


def level_from_points(total_points):
    # A simple level curve keeps progress understandable and easy to communicate.
    total_points = max(0, int(total_points or 0))
    level = total_points // 250 + 1
    progress = (total_points % 250) / 250.0
    remaining = 250 - (total_points % 250)
    return level, progress, remaining


def init_session_defaults(st_module):
    # Initialize widget state once so reruns do not reset the user's selected controls.
    defaults = {
        "transcribed_text": "",
        "current_result": None,
        "current_argument": "",
        "preset_choice": "Balanced default",
        "mode_choice": "debate",
        "style_choice": "Formal",
        "topic_choice": "General",
        "intensity_choice": 3,
    }
    for key, value in defaults.items():
        if key not in st_module.session_state:
            st_module.session_state[key] = value
