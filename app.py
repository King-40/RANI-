"""
Jarvis web server (Gemini version, works for phone + computer through the browser).

Environment variables:
    GEMINI_API_KEY   your key from https://aistudio.google.com/apikey
    APP_PASSWORD     any password you choose (protects your key from strangers)
    GEMINI_MODEL     optional, default below

Run locally:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""

import os

import requests
from flask import Flask, jsonify, request, send_from_directory

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
API_KEY = os.environ.get("GEMINI_API_KEY", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

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


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


@app.post("/chat")
def chat():
    # Protects your API key if the app is hosted publicly
    if APP_PASSWORD and request.headers.get("X-Password", "") != APP_PASSWORD:
        return jsonify(error="unauthorized"), 401

    data = request.get_json(force=True, silent=True) or {}
    msgs = [
        m for m in data.get("messages", [])[-30:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    if not msgs:
        return jsonify(error="empty"), 400

    contents = [
        {
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": str(m["content"])}],
        }
        for m in msgs
    ]

    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            headers={"x-goog-api-key": API_KEY, "Content-Type": "application/json"},
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": contents,
                "generationConfig": {"maxOutputTokens": 800, "temperature": 0.9},
            },
            timeout=30,
        )
        if r.status_code == 429:
            return jsonify(error="rate_limited"), 429
        r.raise_for_status()
        parts = r.json()["candidates"][0]["content"]["parts"]
        reply = "".join(p.get("text", "") for p in parts).strip()
        if not reply:
            reply = "Sir, mujhe samajh nahi aaya. Dobara bologe?"
        return jsonify(reply=reply)
    except Exception as e:
        print("Error:", e)
        return jsonify(error="server_error"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
