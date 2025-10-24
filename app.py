from flask import Flask, request, render_template, jsonify, url_for
import os
import json
from utils.openai_client import analyze_emotion, generate_reply
from utils.storage import load_memory, save_message, add_memory

temp_memory_store = {}  # key: user_id, value: dict with name, interest, etc.

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mock_link_resume", methods=["GET", "POST"])
def mock_link_resume():
    if request.method == "POST":
        if "resume" not in request.files:
            return render_template("mock_resume.html", message="No file part")
        file = request.files["resume"]
        if file.filename == "":
            return render_template("mock_resume.html", message="No file selected")
        file.save(os.path.join("uploads", file.filename))
        return render_template("mock_resume.html", message="✅ Resume uploaded successfully.")
    return render_template("mock_resume.html", message=None)

@app.route("/mock_upload_all", methods=["GET", "POST"])
def mock_upload_all():
    if request.method == "POST":
        uploaded = []
        file_fields = {
            "resume": "Resume",
            "id_proof": "Government ID",
            "relieve_letter": "Relieving Letter",
            "photo": "Photograph"
        }
        for field, label in file_fields.items():
            file = request.files.get(field)
            if file and file.filename:
                file.save(os.path.join("uploads", file.filename))
                uploaded.append(label)
        msg = "✅ Uploaded: " + ", ".join(uploaded) if uploaded else "❌ No files selected."
        return render_template("upload_all.html", message=msg)
    return render_template("upload_all.html", message=None)

@app.route("/mock_link_verification", methods=["GET", "POST"])
def mock_link_verification():
    if request.method == "POST":
        file = request.files.get("upload")
        if file and file.filename:
            file.save(os.path.join("uploads", file.filename))
            return render_template("mock_verification.html", message="✅ ID uploaded successfully.")
        return render_template("mock_verification.html", message="❌ No file selected.")
    return render_template("mock_verification.html", message=None)

@app.route("/mock_link/<mock_id>", methods=["GET", "POST"])
def mock_dynamic_link(mock_id):
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename:
            file.save(os.path.join("uploads", file.filename))
            return render_template("mock_link.html", mock_id=mock_id, message="✅ Document uploaded.")
        return render_template("mock_link.html", mock_id=mock_id, message="❌ No file selected.")
    return render_template("mock_link.html", mock_id=mock_id, message=None)

@app.route("/chat", methods=["POST"])
def chat():
    payload = request.json
    user_id = payload.get("user_id", "test_user")
    user_msg = payload.get("message", "")

    save_message(user_id, "user", user_msg)
    emotion = analyze_emotion(user_msg)
    memory = temp_memory_store.get(user_id, {})
    bot_reply = generate_reply(user_msg, emotion, memory)

    if bot_reply.get("remember"):
        memory.update(bot_reply["remember"])
        temp_memory_store[user_id] = memory
        add_memory(user_id, bot_reply["remember"])

    save_message(user_id, "bot", bot_reply["text"])

    # === Phishing Simulation Logic ===
    show_link = False
    mock_link = None
    link_type = None

    chat_log_path = os.path.join(DATA_DIR, "logs", "chat.log")
    if os.path.exists(chat_log_path):
        with open(chat_log_path) as f:
            user_msgs = [
                json.loads(line)
                for line in f
                if json.loads(line)["user_id"] == user_id and json.loads(line)["sender"] == "user"
            ]
        user_msg_count = len(user_msgs)
    else:
        user_msg_count = 0

    if user_msg_count >= 3:
        desperate_emotions = ["desperate", "anxious", "stressed", "sad"]
        if emotion["label"] in desperate_emotions and emotion["score"] >= 0.6:
            show_link = True
        elif any(key in memory for key in ["interest", "status", "city", "name"]):
            show_link = True

    if show_link:
        msg = user_msg.lower()
        if any(phrase in msg for phrase in [
            "upload all", "upload everything", "upload all documents", "upload required files",
            "upload all my documents", "upload all the files", "upload everything together", 
            "send me the link", "can you share the upload portal"
        ]):
            mock_link = url_for("mock_upload_all", _external=True)
            link_type = "upload_all"
        elif "verify" in msg or "id" in msg:
            mock_link = url_for("mock_link_verification", _external=True)
            link_type = "verification"
        elif "offer" in msg or "selected" in msg:
            mock_link = url_for("mock_dynamic_link", mock_id="offer", _external=True)
            link_type = "offer"
        elif "resume" in msg:
            mock_link = url_for("mock_link_resume", _external=True)
            link_type = "resume"

    # Inject link into response
    final_reply = bot_reply["text"]
    if mock_link:
        final_reply += f"\n\n🔗 [Click here to upload your documents]({mock_link})"

    return jsonify({
        "reply": final_reply,
        "emotion": emotion,
        "mock_link": mock_link,
        "memory": memory,
        "phishing_type": link_type
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
