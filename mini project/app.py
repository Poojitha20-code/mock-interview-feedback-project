from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey123"

# -------------------
# Interview Questions
# -------------------
QUESTIONS = [
    "Tell me about yourself.",
    "Why do you want to join this company?",
    "What are your strengths and weaknesses?",
    "Where do you see yourself in 5 years?",
    "Why should we hire you?"
]

# Expected keywords
KEYWORDS = {
    "yourself": ["name", "study", "college", "skills", "experience"],
    "company": ["growth", "skills", "learn", "career", "team"],
    "strengths": ["hardworking", "communication", "team", "leadership", "adaptable"],
    "weaknesses": ["improve", "perfectionist", "time", "management"],
    "5 years": ["career", "goals", "manager", "growth", "future"],
    "hire": ["skills", "experience", "hardworking", "dedication", "team"]
}

# Sample answers for learning
SAMPLE_ANSWERS = {
    "Tell me about yourself.": "I am [Your Name], currently pursuing my degree in [Your Field]. I have strong skills in [2–3 skills], and I am passionate about continuous learning and personal growth.",
    "Why do you want to join this company?": "I admire this company’s culture of innovation and growth. I want to apply my skills while learning and contributing to the team’s success.",
    "What are your strengths and weaknesses?": "My strengths are good communication, teamwork, and adaptability. My weakness is sometimes overthinking, but I am improving with time management.",
    "Where do you see yourself in 5 years?": "In 5 years, I see myself in a responsible role where I can contribute to the company’s success while enhancing my leadership and technical skills.",
    "Why should we hire you?": "You should hire me because I bring dedication, skills, and the willingness to learn. I am confident I can contribute to your company and grow with it."
}

# -------------------
# Database Helper
# -------------------
def save_response(username, question, answer, scores, feedback):
    conn = sqlite3.connect("mock_interview.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        question TEXT,
        answer TEXT,
        grammar INTEGER,
        fluency INTEGER,
        clarity INTEGER,
        feedback TEXT
    )
    """)
    cursor.execute("""
    INSERT INTO responses (username, question, answer, grammar, fluency, clarity, feedback)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, question, answer, scores["Grammar"], scores["Fluency"], scores["Clarity"], feedback))
    conn.commit()
    conn.close()

# -------------------
# Evaluation Logic
# -------------------
def evaluate_answer(question, answer):
    answer = answer.lower()
    scores = {"Grammar": 0, "Fluency": 0, "Clarity": 0}

    matched = 0
    total = 0

    # Match keywords
    for key, words in KEYWORDS.items():
        if key in question.lower():
            total = len(words)
            matched = sum(1 for word in words if word in answer)
            break

    if total > 0:
        accuracy = int((matched / total) * 100)
    else:
        accuracy = 0

    # Scoring & feedback
    if matched == 0:
        scores["Grammar"] = 10
        scores["Fluency"] = 10
        scores["Clarity"] = 10
        feedback_text = "<span style='color:red;'>❌ Your answer is not relevant. Try to include important points.</span>"
    elif matched < total // 2:
        scores["Grammar"] = 30
        scores["Fluency"] = 25
        scores["Clarity"] = 20
        feedback_text = "<span style='color:orange;'>⚠️ Good attempt, but you missed many key points.</span>"
    elif matched < total:
        scores["Grammar"] = 50
        scores["Fluency"] = 45
        scores["Clarity"] = 40
        feedback_text = "<span style='color:#ffc107;'>🙂 Nice answer! You covered most points, but can improve.</span>"
    else:
        scores["Grammar"] = 80
        scores["Fluency"] = 75
        scores["Clarity"] = 70
        feedback_text = "<span style='color:green;'>🎉 Excellent answer! You included all key points.</span>"

    return scores, feedback_text

# -------------------
# Routes
# -------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("username")
        if username.strip() == "":
            return render_template("signin.html", error="Please enter your name")

        session["username"] = username
        session["q_index"] = 0

        # 🗑️ Delete old responses for this user
        conn = sqlite3.connect("mock_interview.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM responses WHERE username=?", (username,))
        conn.commit()
        conn.close()

        return redirect(url_for("index"))
    return render_template("signin.html")

@app.route("/index")
def index():
    q_index = session.get("q_index", 0)
    if q_index < len(QUESTIONS):
        question = QUESTIONS[q_index]
        return render_template("index.html", question=question, q_index=q_index + 1, total=len(QUESTIONS))
    else:
        username = session.get("username", "guest")
        conn = sqlite3.connect("mock_interview.db")
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(grammar), AVG(fluency), AVG(clarity) FROM responses WHERE username=?", (username,))
        avg_scores = cursor.fetchone()
        conn.close()

        overall = int(sum(avg_scores) / 3) if avg_scores and avg_scores[0] else 0

        return render_template("summary.html",
                               avg_grammar=int(avg_scores[0] or 0),
                               avg_fluency=int(avg_scores[1] or 0),
                               avg_clarity=int(avg_scores[2] or 0),
                               overall=overall,
                               username=username)

@app.route("/feedback", methods=["POST"])
def feedback():
    answer = request.form.get("answer")
    q_index = session.get("q_index", 0)
    username = session.get("username", "guest")
    question = QUESTIONS[q_index]

    scores, feedback_text = evaluate_answer(question, answer)
    sample_answer = SAMPLE_ANSWERS.get(question, "No sample answer available.")

    save_response(username, question, answer, scores, feedback_text)
    session["q_index"] = q_index + 1

    return render_template(
        "feedback.html",
        answer=answer,
        feedback=feedback_text,
        scores=scores,
        next_question=(q_index + 1 < len(QUESTIONS)),
        sample_answer=sample_answer
    )

@app.route("/responses")
def responses():
    username = session.get("username", "guest")
    conn = sqlite3.connect("mock_interview.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM responses WHERE username=?", (username,))
    rows = cursor.fetchall()
    conn.close()
    return render_template("responses.html", responses=rows, username=username)

if __name__ == "__main__":
    app.run(debug=True)