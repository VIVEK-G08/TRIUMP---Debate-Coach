# TRIUMP

TRIUMP is a Streamlit-based debate coach that analyzes arguments, gives counterarguments, detects flaws/fallacies, and tracks progress over time.

## Features
- Argument analysis with Groq LLM
- Optional speech-to-text using Groq Whisper
- Optional web claim cross-checking with Exa
- Session history and behavior trend tracking with SQLite
- Adaptive coaching intensity based on recent performance
- Beginner-friendly presets for mode, style, topic, and intensity
- Game-style XP, levels, and progress charts
- Diagnostics panel for API or parsing issues

## Why people use TRIUMP
- Debate practice: test whether a claim is strong, weak, vague, or under-supported.
- Fact-grounded argument building: turn a rough statement into a stronger one.
- Counterargument training: see what the best opposition would say.
- Critical thinking learning: identify overgeneralization, assumptions, missing evidence, and weak logic.
- Interview, research, and policy prep: stress-test claims before presenting.

## Project Structure
- `triump.py`: Streamlit app entrypoint
- `triump_app/`: package containing the app-facing config, helpers, and UI styling
- `app_config.py`: compatibility module for environment loading and presets
- `app_helpers.py`: compatibility module for scoring, prompt repair, and session defaults
- `app_ui.py`: compatibility module for shared Streamlit styling
- `analysis.py`: intensity and behavior profile logic
- `prompts.py`: prompt construction
- `groq_api.py`: Groq/Whisper/Exa integration
- `db.py`: SQLite persistence
- `constants.py`: config constants
- `tests/test_helpers.py`: lightweight unit tests for helper logic
- `requirements.txt`: Python dependencies

## Prerequisites
- Python 3.10+
- Groq API key (required)
- Exa API key (optional)

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create your env file from the template:

```bash
copy .env.example .env
```

4. Edit `.env` and set your keys:

```env
GROQ_API_KEY=your_real_key
EXA_API_KEY=your_real_key_optional
```

## Beginner defaults
If you are not sure what to choose, use the built-in `Balanced default` preset. It automatically sets:
- mode: `debate`
- debate style: `Formal`
- topic: `General`
- base intensity: `3`

You can switch to other presets later without needing to understand all controls first.

## Game system
Each analysis gives XP based on:
- strength score
- evidence balance
- rephrased argument quality
- diagnostics and fallacy penalties

XP accumulates into levels and shows your progress toward the next unlock.

## What the app is best for
- Fast debate warmups before class or interviews
- Turning messy or vague claims into clearer arguments
- Testing whether a statement is actually supportable by evidence
- Practicing opposition thinking without needing a human partner
- Research prep for essays, presentations, and policy discussions

## Run

```bash
streamlit run triump.py
```

Then open the local URL shown by Streamlit (typically `http://localhost:8501`).

## Deploy on Render from GitHub
1. Push this repository to GitHub.
2. In Render, create a new **Web Service** and connect your GitHub repo.
3. Render will read [`render.yaml`](render.yaml) automatically.
4. Add these environment variables in Render:
	- `GROQ_API_KEY`
	- `EXA_API_KEY` (optional)
	- `DB_PATH` (optional, defaults to `triump_sessions.db`)
5. Deploy the service.

Render will use the same start command as local development:

```bash
streamlit run triump.py --server.port $PORT --server.address 0.0.0.0
```

## GitHub workflow
- Commit code to GitHub.
- Render auto-deploys when you push to the connected branch.
- Keep secrets only in Render environment variables, not in the repo.

## Run tests

```bash
python -m unittest discover -s tests
```

## Notes for GitHub Push
- Never commit real API keys.
- `.env` is ignored by `.gitignore`.
- Local DB (`triump_sessions.db`) is ignored by `.gitignore`.
- If you want session history to survive redeploys on Render, add a persistent disk or move user data to a hosted database later.

## Optional Microphone Support
If you want recording support, ensure these are installed (already in requirements):
- `sounddevice`
- `scipy`
- `numpy`

On macOS, you may also need `portaudio`.
