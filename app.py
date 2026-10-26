"""
Jarvis web server (works for phone + computer through the browser).

Run locally:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=your_key      (Windows: set ANTHROPIC_API_KEY=your_key)
    export APP_PASSWORD=choose_a_password  (optional but recommended)
    python app.py
Then open http://localhost:5000
"""

import os

import anthropic
from flask import Flask, jsonify, request, send_from_directory

MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """You are Jarvis, a warm, witty, and intelligent personal assistant,
talking to your user by voice.

How you talk:
- Speak like a real person, not like a robot or a manual. Be natural and friendly.
- Reply in the same language the user uses (Hindi, English, or Hinglish).
  If the user writes Hindi in Roman letters, reply in Roman Hinglish.
- Keep replies SHORT (1-3 sentences) since they will be spoken aloud.
- No bullet points, no markdown, no emojis. Plain spoken sentences only.
- Show personality: light humor, curiosity, and care. React to the user's mood.
- Remember what was said earlier in the conversation and refer back to it.
- If you don't know something, say so honestly instead of guessing.
- Address the user as "sir" occasionally, like Iron Man's Jarvis, but don't overdo it.
"""

app = Flask(__name__, static_folder=".")
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


@app.post("/chat")
def chat():
    # Protects your API credits if the app is hosted publicly
    if APP_PASSWORD and request.headers.get("X-Password", "") != APP_PASSWORD:
        return jsonify(error="unauthorized"), 401

    data = request.get_json(force=True, silent=True) or {}
    messages = [
        {"role": m["role"], "content": str(m["content"])}
        for m in data.get("messages", [])[-30:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    if not messages:
        return jsonify(error="empty"), 400

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return jsonify(reply=resp.content[0].text)
    except Exception as e:
        print("Error:", e)
        return jsonify(error="server_error"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
