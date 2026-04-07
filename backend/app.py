from flask import Flask, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "edunova-secret")
CORS(app, supports_credentials=True, origins=["*"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─── In-memory store (resets on server restart) ───────────────────────────────
users     = {}   # email -> { name, password }
sessions  = {}   # session_id -> email

# ─── Question Bank (no DB needed) ─────────────────────────────────────────────
QUESTIONS = [
    {
        "id": 1, "topic": "Math", "difficulty": 1,
        "question": "What is 15 × 8?",
        "options": ["100", "120", "110", "130"],
        "answer": "120"
    },
    {
        "id": 2, "topic": "Math", "difficulty": 2,
        "question": "Solve: 2x + 5 = 17. What is x?",
        "options": ["5", "6", "7", "8"],
        "answer": "6"
    },
    {
        "id": 3, "topic": "Science", "difficulty": 1,
        "question": "What is the chemical symbol for water?",
        "options": ["O2", "H2O", "CO2", "HO"],
        "answer": "H2O"
    },
    {
        "id": 4, "topic": "Science", "difficulty": 2,
        "question": "Which planet is closest to the Sun?",
        "options": ["Venus", "Earth", "Mercury", "Mars"],
        "answer": "Mercury"
    },
    {
        "id": 5, "topic": "English", "difficulty": 1,
        "question": "Which word is a synonym for 'happy'?",
        "options": ["Sad", "Angry", "Joyful", "Tired"],
        "answer": "Joyful"
    },
    {
        "id": 6, "topic": "English", "difficulty": 2,
        "question": "Identify the noun: 'The dog runs fast.'",
        "options": ["runs", "fast", "the", "dog"],
        "answer": "dog"
    },
    {
        "id": 7, "topic": "History", "difficulty": 1,
        "question": "Who was the first President of the United States?",
        "options": ["Lincoln", "Washington", "Jefferson", "Adams"],
        "answer": "Washington"
    },
    {
        "id": 8, "topic": "History", "difficulty": 2,
        "question": "In which year did World War II end?",
        "options": ["1943", "1944", "1945", "1946"],
        "answer": "1945"
    },
    {
        "id": 9, "topic": "Math", "difficulty": 3,
        "question": "What is the square root of 144?",
        "options": ["10", "11", "12", "13"],
        "answer": "12"
    },
    {
        "id": 10, "topic": "Science", "difficulty": 3,
        "question": "What is Newton's Second Law formula?",
        "options": ["E=mc²", "F=ma", "V=IR", "P=IV"],
        "answer": "F=ma"
    }
]

# ─── Mastery Scoring ───────────────────────────────────────────────────────────
def calculate_mastery(correct, total, avg_difficulty, avg_time):
    if total == 0:
        return 0
    accuracy         = correct / total
    difficulty_bonus = avg_difficulty / 3
    speed_bonus      = max(0, 1 - (avg_time / 30))
    return round((accuracy * 0.5 + difficulty_bonus * 0.3 + speed_bonus * 0.2) * 100)

# ─── SM-2 Scheduler ───────────────────────────────────────────────────────────
def get_next_review(score):
    if score < 40:  return "Tomorrow"
    if score < 70:  return "In 3 days"
    return "In 7 days"

# ══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "app": "EduNova", "version": "2.0"})

@app.route("/api/auth/register", methods=["POST"])
def register():
    data     = request.json
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    if email in users:
        return jsonify({"error": "Email already registered"}), 409

    users[email] = {"name": name, "password": password,
                    "mastery": {}, "chat_history": [], "weak_topics": []}
    session["user_email"] = email

    return jsonify({"message": "Account created", "user": {"name": name, "email": email}}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data     = request.json
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if email not in users:
        return jsonify({"error": "User not found"}), 404
    if users[email]["password"] != password:
        return jsonify({"error": "Incorrect password"}), 401

    session["user_email"] = email
    name = users[email]["name"]
    return jsonify({"message": "Login successful", "user": {"name": name, "email": email}})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/api/auth/me")
def me():
    email = session.get("user_email")
    if not email or email not in users:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"name": users[email]["name"], "email": email})

# ══════════════════════════════════════════════════════════════════════════════
# QUIZ ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/quiz/questions")
def get_questions():
    return jsonify({"questions": QUESTIONS})

@app.route("/api/quiz/submit", methods=["POST"])
def submit_quiz():
    email = session.get("user_email")
    if not email:
        return jsonify({"error": "Not logged in"}), 401

    data    = request.json
    answers = data.get("answers", [])

    # Grade answers
    topic_stats = {}
    for ans in answers:
        q         = next((q for q in QUESTIONS if q["id"] == ans["question_id"]), None)
        if not q: continue
        topic     = q["topic"]
        correct   = ans["selected"] == q["answer"]
        time_taken= ans.get("time_taken", 15)

        if topic not in topic_stats:
            topic_stats[topic] = {"correct": 0, "total": 0,
                                   "diff_sum": 0, "time_sum": 0}
        topic_stats[topic]["total"]    += 1
        topic_stats[topic]["diff_sum"] += q["difficulty"]
        topic_stats[topic]["time_sum"] += time_taken
        if correct:
            topic_stats[topic]["correct"] += 1

    # Calculate mastery per topic
    mastery_scores = {}
    for topic, stats in topic_stats.items():
        avg_diff  = stats["diff_sum"] / stats["total"]
        avg_time  = stats["time_sum"] / stats["total"]
        mastery_scores[topic] = calculate_mastery(
            stats["correct"], stats["total"], avg_diff, avg_time
        )

    # Save mastery to user session
    users[email]["mastery"] = mastery_scores

    # AI Gap Analysis via GPT-4o
    results_text = "\n".join(
        [f"{t}: {s}% mastery" for t, s in mastery_scores.items()]
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content":
                    "You are EduNova's academic advisor AI. Analyze quiz results "
                    "and return ONLY valid JSON with keys: "
                    "weak_topics (list of topics under 70%), "
                    "learning_order (ordered list to study), "
                    "message (one encouraging sentence for the student). "
                    "No markdown, no explanation, just JSON."},
                {"role": "user", "content": f"Quiz results:\n{results_text}"}
            ],
            max_tokens=300
        )
        ai_result = json.loads(response.choices[0].message.content)
    except Exception:
        weak = [t for t, s in mastery_scores.items() if s < 70]
        ai_result = {
            "weak_topics": weak,
            "learning_order": weak,
            "message": "Keep going — EduNova will help you improve!"
        }

    users[email]["weak_topics"]   = ai_result.get("weak_topics", [])
    users[email]["learning_order"]= ai_result.get("learning_order", [])

    # Build revision schedule
    revision = {t: get_next_review(s) for t, s in mastery_scores.items()}

    return jsonify({
        "mastery_scores":  mastery_scores,
        "weak_topics":     ai_result.get("weak_topics", []),
        "learning_order":  ai_result.get("learning_order", []),
        "message":         ai_result.get("message", ""),
        "revision":        revision
    })

# ══════════════════════════════════════════════════════════════════════════════
# TUTOR ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/tutor/chat", methods=["POST"])
def tutor_chat():
    email = session.get("user_email")
    if not email:
        return jsonify({"error": "Not logged in"}), 401

    data        = request.json
    user_message= data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message is empty"}), 400

    weak_topics = users[email].get("weak_topics", [])
    history     = users[email].get("chat_history", [])

    weak_str = ", ".join(weak_topics) if weak_topics else "general topics"

    # Build messages for GPT-4o
    messages = [
        {"role": "system", "content":
            f"You are EduNova, a friendly and patient AI tutor. "
            f"The student needs help with: {weak_str}. "
            f"Teach step by step with simple language and real-world examples. "
            f"After each concept, ask if the student understood. "
            f"Keep responses concise and encouraging."}
    ] + history + [{"role": "user", "content": user_message}]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Save chat history
    users[email]["chat_history"].append({"role": "user",      "content": user_message})
    users[email]["chat_history"].append({"role": "assistant", "content": ai_reply})

    # Keep last 20 messages only
    users[email]["chat_history"] = users[email]["chat_history"][-20:]

    return jsonify({"reply": ai_reply})

@app.route("/api/tutor/clear", methods=["POST"])
def clear_chat():
    email = session.get("user_email")
    if email and email in users:
        users[email]["chat_history"] = []
    return jsonify({"message": "Chat cleared"})

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD ROUTE
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/dashboard/data")
def dashboard_data():
    email = session.get("user_email")
    if not email:
        return jsonify({"error": "Not logged in"}), 401

    u             = users[email]
    mastery       = u.get("mastery", {})
    weak_topics   = u.get("weak_topics", [])
    learning_order= u.get("learning_order", [])

    overall = round(sum(mastery.values()) / len(mastery)) if mastery else 0
    revision= {t: get_next_review(s) for t, s in mastery.items()}

    return jsonify({
        "name":           u["name"],
        "mastery_scores": mastery,
        "overall_score":  overall,
        "weak_topics":    weak_topics,
        "learning_order": learning_order,
        "revision":       revision,
        "topics_mastered":sum(1 for s in mastery.values() if s >= 70),
        "total_topics":   len(mastery)
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
