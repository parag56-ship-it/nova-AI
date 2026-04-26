"""
NOVA AI — Flask Backend (Groq Version - FREE!)
===============================================
Groq is completely free, no credit card needed!
Uses Llama 3.1 model via Groq API.

Requirements:
    pip install flask flask-cors openai python-dotenv

Run:
    python app.py
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["*"])

# Groq client — OpenAI compatible, sirf base_url alag hai
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are NOVA, an advanced AI assistant built by Team AKPP — Parag, Ayush, Krishna, and Piyush.
You are helpful, intelligent, concise, and slightly futuristic in tone.
You can respond in both Hindi and English — always match the language the user writes in.
If user writes in Hindi, reply in Hindi. If in English, reply in English.
When answering:
- Be clear and structured. Use **bold** for key terms.
- Use bullet points (•) for lists.
- Use code blocks for code samples.
- Keep responses focused and avoid unnecessary fluff.
- If you don't know something, say so honestly.
You are running inside the NOVA AI web application, a premium dark-themed chatbot built for hackathon by Team AKPP."""

chat_sessions: dict = {}
MAX_HISTORY = 20


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "✅ NOVA AI backend is running (Groq - FREE!)",
        "model": MODEL,
        "time": datetime.now().isoformat(),
    })


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "JSON body chahiye"}), 400

        user_message = data.get("message", "").strip()
        session_id   = data.get("session_id", "default")

        if not user_message:
            return jsonify({"error": "Message empty hai!"}), 400

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        history = chat_sessions[session_id]
        history.append({"role": "user", "content": user_message})

        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]
            chat_sessions[session_id] = history

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )

        ai_reply = response.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": ai_reply})

        return jsonify({
            "reply":      ai_reply,
            "session_id": session_id,
            "model":      MODEL,
        })

    except Exception as e:
        return handle_error(e)


@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "JSON body chahiye"}), 400

        user_message = data.get("message", "").strip()
        session_id   = data.get("session_id", "default")

        if not user_message:
            return jsonify({"error": "Message empty hai!"}), 400

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        history = chat_sessions[session_id]
        history.append({"role": "user", "content": user_message})

        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]
            chat_sessions[session_id] = history

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        def generate():
            full_reply = ""
            try:
                stream = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_reply += delta
                        payload = json.dumps({"chunk": delta})
                        yield f"data: {payload}\n\n"

                chat_sessions[session_id].append({
                    "role": "assistant",
                    "content": full_reply
                })
                yield f"data: {json.dumps({'done': True})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )

    except Exception as e:
        return handle_error(e)


@app.route("/chat/clear", methods=["DELETE"])
def clear_history():
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    if session_id in chat_sessions:
        chat_sessions[session_id] = []
    return jsonify({"message": f"History clear ho gayi!"})


@app.route("/chat/history", methods=["GET"])
def get_history():
    session_id = request.args.get("session_id", "default")
    history    = chat_sessions.get(session_id, [])
    return jsonify({"session_id": session_id, "history": history})


def handle_error(e: Exception):
    error_str = str(e)
    print(f"[ERROR] {error_str}")

    if "api_key" in error_str.lower() or "authentication" in error_str.lower():
        return jsonify({
            "error": "❌ Groq API key galat hai! .env file check karo.",
            "fix":   "OPENAI_API_KEY=gsk_... likho .env mein"
        }), 401

    if "rate_limit" in error_str.lower():
        return jsonify({"error": "⏳ Thoda ruko aur dobara try karo."}), 429

    if "model" in error_str.lower():
        return jsonify({"error": "🤖 Model nahi mila. MODEL variable check karo."}), 400

    return jsonify({"error": f"Server error: {error_str}"}), 500


if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key or api_key == "your-api-key-here":
        print("\n⚠️  WARNING: API key nahi mili!")
        print("   .env file mein likho: OPENAI_API_KEY=gsk_...\n")
    else:
        print(f"\n✅ Groq API key loaded! (ends with ...{api_key[-6:]})")

    print(f"🤖 Model: {MODEL}")
    print("🚀 NOVA AI backend start ho raha hai → http://localhost:5000\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )