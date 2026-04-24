
"""
TRIUMP — Debate Coach
Stack: Groq (Llama 4 Scout + Whisper Large v3 Turbo) + Exa + SQLite
Run:   streamlit run triump.py
Keys:  GROQ_API_KEY, EXA_API_KEY  (set as env vars or via Render)
"""

import datetime
import json

import streamlit as st

from analysis import build_behaviour_profile, compute_effective_intensity, intensity_breakdown
from triump_app.config import PRESETS, load_api_keys
from triump_app.helpers import build_repair_prompt, fact_counts, init_session_defaults, level_from_points, session_points as calculate_session_points
from triump_app.ui import APP_STYLE
from constants import COACH_NAME
from db import init_db, load_sessions, save_session
from groq_api import MIC_AVAILABLE, call_groq_llm, exa_fact_check, extract_json, record_mic, transcribe_audio
from prompts import build_debate_prompt

st.set_page_config(page_title="TRIUMP", layout="wide", page_icon="⚔")
st.markdown(APP_STYLE, unsafe_allow_html=True)

init_db()

# Keep common session fields available on every rerun so Streamlit widgets stay stable.
init_session_defaults(st)

groq_key, exa_key = load_api_keys(st)

with st.sidebar:
    st.markdown("## ⚔ TRIUMP")
    st.caption("Debate Coach · Behaviour-Adaptive")
    st.divider()

    st.markdown("**Quick start**")
    # Presets give beginners a safe starting point without needing to understand every control.
    selected_preset = st.selectbox("Preset", list(PRESETS.keys()), key="preset_choice")
    if st.session_state.get("applied_preset") != selected_preset:
        preset = PRESETS.get(selected_preset, PRESETS["Balanced default"])
        st.session_state.mode_choice = preset["mode"]
        st.session_state.style_choice = preset["style"]
        st.session_state.topic_choice = preset["topic"]
        st.session_state.intensity_choice = preset["intensity"]
        st.session_state.applied_preset = selected_preset
    st.caption("Use a preset if you are not sure how to set mode, style, topic, or intensity.")

    st.markdown("**API configuration**")
    # Keys are loaded from .env or deployed environment variables; the UI does not ask for them.
    st.caption("Groq key is loaded automatically from .env or Streamlit secrets.")
    st.caption("Exa key is optional and also auto-loaded if available.")
    if not groq_key:
        st.warning("Groq key not found in environment. Add GROQ_API_KEY to .env.")

    st.divider()

    mode = st.radio("Mode", ["debate","critique","factcheck"],
                    key="mode_choice",
                    format_func=lambda x: {"debate":"⚔  Debate me",
                                           "critique":"🔍  Critique only",
                                           "factcheck":"🔎  Fact-check"}[x])
    debate_style = st.selectbox("Debate style", ["Formal","Casual","Critical"], key="style_choice")
    topic = st.selectbox("Topic", ["General","Education","Politics","Ethics","Science"], key="topic_choice")
    base_intensity = st.slider("Base intensity", 1, 5, key="intensity_choice")

    st.markdown("**How it works**")
    # These controls tune the response style before a user has to learn the full app.
    st.caption("Mode changes the kind of response, style changes the tone, topic adds context, and intensity controls how hard TRIUMP pushes back.")
    st.divider()

    st.markdown("**Speech input** (Groq Whisper — same key)")
    if MIC_AVAILABLE:
        rec_dur = st.slider("Record seconds", 3, 20, 8)
        use_mic = st.checkbox("Enable microphone")
    else:
        st.caption("pip install sounddevice scipy for mic input")
        use_mic = False

    st.divider()

    all_sessions = load_sessions(10)
    badge_items = []
    if sum(1 for s in all_sessions if s['strength_score'] >= 7) >= 3:
        badge_items.append("Strong Logic")
    if sum(1 for s in all_sessions if s['facts']) >= 2:
        badge_items.append("Fact-Checker")
    if len({s['mode'] for s in all_sessions if s['mode'] in ['debate','critique']}) >= 2:
        badge_items.append("Balanced Thinker")
    if badge_items:
        st.markdown("**Badges:** " + " ".join(f'<span class="pill">{b}</span>' for b in badge_items), unsafe_allow_html=True)
    else:
        st.markdown('**Badges:** <span class="pill">No badges yet</span>', unsafe_allow_html=True)

    total_points = sum(int(s.get("points", 0) or 0) for s in all_sessions)
    level, progress, remaining = level_from_points(total_points)
    st.markdown("**Game stats**")
    # XP and levels make the app feel like a progress loop instead of a one-off analyzer.
    st.metric("Level", f"Lv {level}")
    st.metric("Total XP", f"{total_points}")
    st.progress(progress)
    st.caption(f"{remaining} XP to next level")

    recent_scores = [int(s.get("strength_score", 0) or 0) for s in reversed(all_sessions[:10])]
    recent_points = [int(s.get("points", 0) or 0) for s in reversed(all_sessions[:10])]
    if recent_scores:
        with st.expander("📈 Progress trend", expanded=False):
            st.caption("Score trend")
            st.line_chart(recent_scores)
            st.caption("XP per session")
            st.bar_chart(recent_points)

    with st.expander("✨ Why people use TRIUMP", expanded=False):
        st.markdown("- Debate practice: test whether a claim is strong, weak, vague, or under-supported.")
        st.markdown("- Fact-grounded argument building: turn a rough statement into a stronger one.")
        st.markdown("- Counterargument training: see what the best opposition would say.")
        st.markdown("- Critical thinking learning: identify overgeneralization, assumptions, missing evidence, and weak logic.")
        st.markdown("- Interview, research, and policy prep: stress-test claims before presenting.")

    if len(all_sessions) >= 3 and groq_key:
        with st.expander("📊 Behaviour profile", expanded=False):
            # The profile summarizes recurring user patterns and personalizes later coaching.
            with st.spinner("Analyzing patterns..."):
                profile = build_behaviour_profile(all_sessions, groq_key)
            if profile and isinstance(profile, dict):
                st.markdown(f"**Style:** {profile.get('argument_style','—')}")
                st.markdown(f"**Trend:** {profile.get('trend','—')}")
                st.markdown(f"**Avg score:** {profile.get('avg_score','—')}/10")
                st.markdown(f"**Weak spot:** {profile.get('predicted_weakness','—')}")
                st.info(f"Tip: {profile.get('coaching_tip','—')}")
    else:
        profile = None
        if groq_key:
            st.caption(f"{3-len(all_sessions)} more session(s) to unlock behaviour profile.")
        else:
            st.caption("Enter Groq key to begin.")

col_main, col_log = st.columns([3,1], gap="large")

with col_main:
    st.markdown("# Make your argument.")
    st.markdown("**Goal:** Sharpen reasoning, encourage fact-based debate, and build confidence.")
    st.info(f"{COACH_NAME} is your debate coach: supportive, challenging, and focused on helping you improve.")

    all_sessions = load_sessions(10)
    # Compute the current intensity from prior sessions so the app adapts over time.
    eff = compute_effective_intensity(base_intensity, all_sessions)
    bd  = intensity_breakdown(base_intensity, all_sessions)

    c1, c2, c3 = st.columns(3)
    delta     = eff - base_intensity
    dstr      = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
    eff_color = "#4caf50" if eff <= 2.5 else "#ff9800" if eff <= 4 else "#f44336"

    c1.markdown(f'<div class="mcard"><div class="mcard-label">base intensity</div>'
                f'<div class="mcard-val">{base_intensity}/5</div>'
                f'<div class="mcard-sub">manual</div></div>', unsafe_allow_html=True)

    c2.markdown(f'<div class="mcard"><div class="mcard-label">effective intensity</div>'
                f'<div class="mcard-val" style="color:{eff_color}">{eff:.1f}/5</div>'
                f'<div class="mcard-sub">auto-adjusted ({dstr})</div></div>', unsafe_allow_html=True)

    c3.markdown(f'<div class="mcard"><div class="mcard-label">sessions logged</div>'
                f'<div class="mcard-val">{len(all_sessions)}</div>'
                f'<div class="mcard-sub">{"profile active" if len(all_sessions)>=3 else f"{3-len(all_sessions)} until profile"}</div></div>',
                unsafe_allow_html=True)

    with st.expander("ℹ  Intensity formula breakdown"):
        st.markdown(f"""<div class="formula-box">
effective = base &times; (1 + fallacy_rate) &times; (1 &minus; improvement_trend &times; 0.3)<br><br>
base              = {base_intensity}<br>
fallacy_rate      = {bd['fallacy_rate']}  &nbsp;(avg fallacies/session, last 5, capped at 1.0)<br>
improvement_trend = {bd['improvement_trend']}  &nbsp;(score delta last 3 sessions, range &minus;1 to +1)<br>
&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;<br>
result            = <b style="color:#e0e0e0">{bd['effective']}</b><br><br>
<span style="color:#444">
High fallacy rate &rarr; intensity climbs automatically.<br>
Consistent improvement &rarr; intensity backs off slightly.<br>
Getting worse &rarr; intensity increases to force correction.
</span></div>""", unsafe_allow_html=True)

    if use_mic and MIC_AVAILABLE:
        if st.button("🎙 Record now", use_container_width=True):
            if not groq_key:
                st.error("Groq key required for Whisper transcription.")
            else:
                # Record locally, then send the audio to Groq Whisper for transcription.
                with st.spinner(f"Recording {rec_dur}s — speak now..."):
                    wav_bytes = record_mic(rec_dur)
                with st.spinner("Transcribing via Groq Whisper Large v3 Turbo..."):
                    transcribed = transcribe_audio(wav_bytes, groq_key)
                if "error" in transcribed.lower():
                    st.error(transcribed)
                else:
                    st.session_state.transcribed_text = transcribed
                    st.success(f"Heard: {transcribed}")

    argument = st.text_area("Your argument",
                             value=st.session_state.transcribed_text,
                             height=150,
                             placeholder="State your position clearly. The AI will accept your argument, then counter it and analyze facts.")

    st.caption("The AI will first accept your argument, then provide a counterargument, fact analysis, and targeted improvement tips.")
    run_btn = st.button("⚔  Analyze argument", type="primary",
                        use_container_width=True,
                        disabled=(not argument.strip()))

    st.markdown("<div class='formula-box'>Score: 1-10, higher is better. Fallacy count is the number of weak or unsupported moves found. Improvement tips show how to make your next argument stronger.</div>", unsafe_allow_html=True)

    if not groq_key:
        st.caption("Set GROQ_API_KEY in .env to run analysis.")

    if run_btn and argument.strip() and not groq_key:
        st.error("Groq API key is missing. Add GROQ_API_KEY in .env and rerun.")

    if run_btn and argument.strip() and groq_key:
        # Build the first prompt, then optionally repair the response if it lacks enough evidence.
        diagnostics = []
        prompt = build_debate_prompt(argument.strip(), mode, eff, profile, debate_style, topic)

        with st.spinner(f"Llama 4 Scout analyzing at intensity {eff:.1f}..."):
            raw = call_groq_llm(prompt, groq_key)

        if isinstance(raw, str) and raw.strip().upper().startswith("ERROR"):
            diagnostics.append(f"Primary Groq call returned: {raw[:300]}")

        result = extract_json(raw)

        if result.get("session_tag") == "parse error":
            diagnostics.append("Primary response JSON parse failed. Fallback parse result used.")

        facts = result.get("facts", []) if isinstance(result, dict) else []
        support_count, counter_count = fact_counts(facts)

        for _ in range(2):
            if support_count >= 6 and counter_count >= 6:
                break
            need_support = max(0, 6 - support_count)
            need_counter = max(0, 6 - counter_count)
            diagnostics.append(
                f"Evidence balance below target (support={support_count}, counter={counter_count}). Running correction pass."
            )
            repair_prompt = build_repair_prompt(
                argument.strip(), mode, eff, profile, debate_style, topic, result, need_support, need_counter
            )
            repair_raw = call_groq_llm(repair_prompt, groq_key)
            if isinstance(repair_raw, str) and repair_raw.strip().upper().startswith("ERROR"):
                diagnostics.append(f"Correction pass returned: {repair_raw[:300]}")
                break
            repaired = extract_json(repair_raw)
            if repaired.get("session_tag") == "parse error":
                diagnostics.append("Correction response JSON parse failed; keeping previous result.")
                break
            result = repaired
            facts = result.get("facts", []) if isinstance(result, dict) else []
            support_count, counter_count = fact_counts(facts)

        if support_count < 6 or counter_count < 6:
            diagnostics.append(
                f"Final evidence counts still below ideal: support={support_count}, counter={counter_count}."
            )

        earned_points = calculate_session_points(result, support_count, counter_count, diagnostics)

        exa_results = []
        # Exa cross-checks the extracted claims so the app can separate model output from web evidence.
        fact_claims = [f["claim"] for f in result.get("facts",[]) if "claim" in f]
        if fact_claims and exa_key:
            with st.spinner("Exa cross-checking claims..."):
                exa_results = exa_fact_check(fact_claims, exa_key)
            exa_notes = [e for e in exa_results if "Exa" in str(e.get("note", ""))]
            if exa_notes:
                diagnostics.append(
                    f"Exa returned {len(exa_notes)} search note(s). First note: {exa_notes[0].get('note','unknown')}"
                )
        elif fact_claims and not exa_key:
            diagnostics.append("Exa key missing: web cross-check skipped.")

        session_data = {
            "argument":            argument.strip(),
            "mode":                mode,
            "base_intensity":      base_intensity,
            "effective_intensity": eff,
            "strength_score":      result.get("strength_score",0),
            "fallacy_count":       result.get("fallacy_count",0),
            "fallacy_types":       result.get("fallacy_types",[]),
            "session_tag":         result.get("session_tag",""),
            "counterargument":     result.get("counterargument",""),
            "flaws":               result.get("flaws",[]),
            "facts":               result.get("facts",[]),
            "points":              earned_points,
        }
        save_session(session_data)
        # Cache the latest result in session state so the right-side analysis panel stays visible.
        st.session_state.transcribed_text = ""
        st.session_state.current_argument = argument.strip()
        st.session_state.current_result = {
            "argument": argument.strip(),
            "result": result,
            "exa_results": exa_results,
            "diagnostics": diagnostics,
            "points": earned_points,
            "mode": mode,
            "effective_intensity": eff,
            "timestamp": datetime.datetime.now().isoformat()
        }

if st.session_state.current_result:
    display = st.session_state.current_result
    result = display["result"]
    exa_results = display.get("exa_results", [])
    diagnostics = display.get("diagnostics", [])

    st.divider()
    st.markdown("### 🎯 Last analysis — persistent until you hit OK")
    # The top row gives a quick health-check before the user reads the full explanation.
    st.markdown(f"**Argument:** {display['argument']}")
    st.markdown(f"**Mode:** {display['mode']} · **Intensity:** {display['effective_intensity']}/5")

    score   = result.get("strength_score",0)
    s_color = "#4caf50" if score>=7 else "#ff9800" if score>=4 else "#f44336"
    session_points = int(display.get("points", 0) or 0)
    total_points = sum(int(s.get("points", 0) or 0) for s in load_sessions(50))
    level, progress, remaining = level_from_points(total_points)

    sc1,sc2,sc3,sc4,sc5 = st.columns(5)
    sc1.markdown(f'<div class="mcard"><div class="mcard-label">strength</div>'
                 f'<div class="mcard-val" style="color:{s_color}">{score}/10</div>'
                 f'<div class="mcard-sub">{result.get("strength_label","—")}</div></div>',
                 unsafe_allow_html=True)
    sc2.markdown(f'<div class="mcard"><div class="mcard-label">fallacies</div>'
                 f'<div class="mcard-val">{result.get("fallacy_count",0)}</div>'
                 f'<div class="mcard-sub">detected</div></div>', unsafe_allow_html=True)
    sc3.markdown(f'<div class="mcard"><div class="mcard-label">claims</div>'
                 f'<div class="mcard-val">{len(result.get("facts",[]))}</div>'
                 f'<div class="mcard-sub">extracted</div></div>', unsafe_allow_html=True)
    sc4.markdown(f'<div class="mcard"><div class="mcard-label">intensity used</div>'
                 f'<div class="mcard-val">{display["effective_intensity"]:.1f}</div>'
                 f'<div class="mcard-sub">formula output</div></div>', unsafe_allow_html=True)
    sc5.markdown(f'<div class="mcard"><div class="mcard-label">xp earned</div>'
                 f'<div class="mcard-val">{session_points}</div>'
                 f'<div class="mcard-sub">level {level}</div></div>', unsafe_allow_html=True)

    st.progress(progress)
    st.caption(f"Level {level} · {remaining} XP to next level · Total XP {total_points}")

    if score >= 7:
        st.success("Strong point! Keep building on this reasoning.")
    elif score >= 4:
        st.info("Good effort — a few clear improvements will make this much stronger.")
    else:
        st.warning("Nice start. Focus on clarity and evidence to improve your position.")

    if result.get("summary"):
        st.markdown(f"**Summary:** {result.get('summary')}")

    if diagnostics:
        # Diagnostics are shown only when something in the pipeline needs attention.
        with st.expander(f"🧰 Diagnostics ({len(diagnostics)})", expanded=True):
            for i, msg in enumerate(diagnostics, 1):
                st.markdown(f"**{i}.** {msg}")

    if result.get("reframed_argument"):
        with st.expander("🛠 Stronger rephrased argument", expanded=True):
            st.markdown(result.get("reframed_argument"))

    if result.get("counterargument"):
        with st.expander("⚔  Counterargument", expanded=True):
            st.markdown(result["counterargument"])

    flaws = result.get("flaws",[])
    if flaws:
        with st.expander(f"🔥  Logical flaws ({len(flaws)})", expanded=True):
            for i,f in enumerate(flaws,1):
                st.markdown(f"**{i}.** {f}")

    facts = result.get("facts",[])
    if facts:
        # Split support and counter evidence so the user sees both sides of the claim.
        with st.expander(f"🔎  Fact check ({len(facts)} claims)", expanded=True):
            for f in facts:
                v   = f.get("verdict","?")
                css = f"v-{v.replace(' ','-')}"
                stance = f.get("stance", "").strip().lower()
                stance_label = f"[{stance.upper()}] " if stance in ["support", "counter"] else ""
                source_hint = f.get("source_hint", "")
                source_part = f"  |  source: {source_hint}" if source_hint else ""
                st.markdown(
                    f'<span class="{css}">[{v.upper()}]</span> {stance_label}**{f.get("claim","") }** — _{f.get("note","") }_{source_part}',
                    unsafe_allow_html=True)
            if exa_results:
                st.markdown("---")
                st.caption("Exa web cross-check:")
                for er in exa_results:
                    verdict = str(er.get('verdict', '')).replace(' ', '-').lower()
                    if verdict == 'error':
                        verdict = 'not-found'
                    css = f"v-{verdict}"
                    src = f" → [{er['source'][:55]}...]({er['source']})" if er.get("source") else ""
                    st.markdown(f'<span class="{css}">[{str(er.get("verdict","not found")).upper()}]</span> {er.get("claim","")}{src}',
                                unsafe_allow_html=True)

        support_facts = [f for f in facts if str(f.get("stance", "")).lower() == "support"]
        counter_facts = [f for f in facts if str(f.get("stance", "")).lower() == "counter"]

        if support_facts:
            with st.expander(f"✅ Support evidence ({len(support_facts)})", expanded=True):
                for i, f in enumerate(support_facts, 1):
                    st.markdown(f"**{i}.** {f.get('claim','')} — _{f.get('note','')}_")

        if counter_facts:
            with st.expander(f"🧪 Counter evidence ({len(counter_facts)})", expanded=True):
                for i, f in enumerate(counter_facts, 1):
                    st.markdown(f"**{i}.** {f.get('claim','')} — _{f.get('note','')}_")

    tag = result.get("session_tag","")
    if tag:
        st.markdown(f'<span class="pill">session: {tag}</span>', unsafe_allow_html=True)

    if result.get("learning_summary"):
        st.markdown(f"**Learning summary:** {result.get('learning_summary')}")

    tips = result.get("improvement_tips", [])
    if tips:
        with st.expander("💡 Improvement tips", expanded=True):
            for i, tip in enumerate(tips, 1):
                st.markdown(f"**{i}.** {tip}")

    with st.expander("📊 Session progress graph", expanded=False):
        history = list(reversed(load_sessions(10)))
        if history:
            st.caption("Strength score trend")
            st.line_chart([int(s.get("strength_score", 0) or 0) for s in history])
            st.caption("XP trend")
            st.bar_chart([int(s.get("points", 0) or 0) for s in history])

    if st.button("OK — close result", use_container_width=True):
        # Clear the persistent result so the UI returns to the input state.
        st.session_state.current_result = None
        st.session_state.current_argument = ""
        st.experimental_rerun()

with col_log:
    st.markdown("### Debate journal")
    latest_sessions = load_sessions(15)
    if latest_sessions:
        log_labels = [f"{s['ts'][:16].replace('T',' ')} · {s['mode']} · {s['session_tag']}" for s in latest_sessions]
        selected_label = st.selectbox("Review past session", log_labels, index=0)
        selected = latest_sessions[log_labels.index(selected_label)]
        st.markdown('<div class="sticky-col">', unsafe_allow_html=True)
        st.markdown(f"**{selected['ts'][:16].replace('T',' ')}**  ·  {selected['mode']}  ·  {selected['session_tag']}")
        st.markdown(f"**Argument:** {selected['argument']}")
        st.markdown(f"**Score:** {selected['strength_score']}/10  ·  **Fallacies:** {selected['fallacy_count']}")
        if selected['counterargument']:
            with st.expander("Past counterargument", expanded=False):
                st.markdown(selected['counterargument'])
        flaws = json.loads(selected['flaws']) if selected['flaws'] else []
        if flaws:
            with st.expander(f"Past flaws ({len(flaws)})", expanded=False):
                for i,f in enumerate(flaws,1):
                    st.markdown(f"**{i}.** {f}")
        facts = json.loads(selected['facts']) if selected['facts'] else []
        if facts:
            with st.expander(f"Past fact analysis ({len(facts)})", expanded=False):
                for f in facts:
                    st.markdown(f"**{f.get('verdict','?').upper()}** — {f.get('claim','')} — _{f.get('note','')}_")
        st.markdown("<div style='margin-top:10px; font-size:12px; color:#888;'>This app is a coach, not professional advice.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("No sessions yet. Start an analysis to populate the log.")
