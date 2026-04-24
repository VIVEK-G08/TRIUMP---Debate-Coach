from __future__ import annotations

import os

from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
# Load local development secrets without requiring the user to paste them into the UI.
load_dotenv(dotenv_path=ENV_PATH, override=True)

PRESETS = {
	"Balanced default": {"mode": "debate", "style": "Formal", "topic": "General", "intensity": 3},
	"Starter mode": {"mode": "critique", "style": "Casual", "topic": "General", "intensity": 2},
	"Fact-check mode": {"mode": "factcheck", "style": "Formal", "topic": "Science", "intensity": 2},
	"Deep debate": {"mode": "debate", "style": "Critical", "topic": "Politics", "intensity": 4},
}


def load_api_keys(st_module):
	# Prefer environment variables, then fall back to Streamlit secrets in hosted deployments.
	env_groq = (os.getenv("GROQ_API_KEY", "") or "").strip()
	env_exa = (os.getenv("EXA_API_KEY", "") or "").strip()
	secret_groq = ""
	secret_exa = ""
	try:
		secret_groq = (st_module.secrets.get("GROQ_API_KEY", "") or "").strip()
		secret_exa = (st_module.secrets.get("EXA_API_KEY", "") or "").strip()
	except Exception:
		secret_groq = ""
		secret_exa = ""
	return env_groq or secret_groq, env_exa or secret_exa
