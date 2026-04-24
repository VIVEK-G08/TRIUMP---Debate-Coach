
import os

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_AUDIO_MODEL = "whisper-large-v3-turbo"
DB_PATH = os.getenv("DB_PATH", "triump_sessions.db")
COACH_NAME = "Jennie"

INTENSITY_TONE = {
    1: "calm and Socratic — ask probing questions, remain measured",
    2: "direct and logical — identify gaps clearly, be fair but firm",
    3: "assertive — challenge every weak assumption, demand rigor",
    4: "aggressive — dismiss weak points bluntly, push for precision",
    5: "brutal — attack every flaw relentlessly, show absolutely no mercy"
}
