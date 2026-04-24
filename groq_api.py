
import io
import json
import re
import time
import requests
from constants import GROQ_CHAT_URL, GROQ_AUDIO_URL, GROQ_CHAT_MODEL, GROQ_AUDIO_MODEL

try:
    import sounddevice as sd
    import numpy as np
    import scipy.io.wavfile as wavfile
    MIC_AVAILABLE = True
except ImportError:
    MIC_AVAILABLE = False

try:
    from exa_py import Exa
    EXA_LIB = True
except ImportError:
    EXA_LIB = False

def call_groq_llm(prompt, api_key, retries=3):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model":       GROQ_CHAT_MODEL,
        "messages":    [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens":  1800,
    }
    for attempt in range(retries):
        try:
            r = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as e:
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            return f"ERROR {r.status_code}: {r.text[:200]}"
        except Exception as e:
            if attempt == retries - 1:
                return f"ERROR: {e}"
            time.sleep(1)
    return "ERROR: max retries"

def extract_json(raw):
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    match   = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {
        "counterargument": cleaned[:600] if cleaned else "No usable output.",
        "flaws": [], "facts": [],
        "strength_score": 0, "strength_label": "unknown",
        "fallacy_count": 0, "fallacy_types": [],
        "session_tag": "parse error"
    }

def transcribe_audio(audio_bytes, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    files   = {
        "file":  ("audio.wav", io.BytesIO(audio_bytes), "audio/wav"),
        "model": (None, GROQ_AUDIO_MODEL),
    }
    try:
        r = requests.post(GROQ_AUDIO_URL, headers=headers, files=files, timeout=60)
        r.raise_for_status()
        return r.json().get("text", "").strip()
    except Exception as e:
        return f"Transcription error: {e}"

def record_mic(duration):
    sr   = 16000
    data = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="int16")
    sd.wait()
    buf = io.BytesIO()
    wavfile.write(buf, sr, data)
    return buf.getvalue()

def exa_fact_check(claims, api_key):
    if not EXA_LIB or not api_key or not claims:
        return [{"claim": c, "verdict": "unverified", "source": "", "note": "Exa not configured"} for c in claims]
    try:
        exa = Exa(api_key=api_key)
        out = []
        for claim in claims[:12]:
            query = re.sub(r"\s+", " ", str(claim)).strip()
            query = re.sub(r"^[\-\*\d\.\)\s]+", "", query)
            query = query[:180]
            try:
                res = exa.search(query, num_results=3, contents=False)
                results = getattr(res, "results", []) or []
                if results:
                    top = results[0]
                    source = getattr(top, "url", "") or ""
                    title = getattr(top, "title", "") or "source found"
                    out.append({"claim": claim, "verdict": "found", "source": source, "note": title})
                else:
                    out.append({"claim": claim, "verdict": "not found", "source": "", "note": "no results"})
            except Exception as e:
                out.append({"claim": claim, "verdict": "not found", "source": "", "note": f"Exa search failed: {e}"})
        return out
    except Exception as e:
        return [{"claim": c, "verdict": "not found", "source": "", "note": f"Exa unavailable: {e}"} for c in claims]
