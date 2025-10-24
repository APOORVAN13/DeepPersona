import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_emotion(text):
    prompt = (
        "You are an assistant that labels the user's emotion from a single sentence. "
        "Return JSON: {\"label\": \"emotion\", \"score\": number}.\n"
        f"Text: {text}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )
    content = resp.choices[0].message.content
    try:
        return eval(content)
    except:
        return {"label": "neutral", "score": 0.5}


def generate_reply(user_text, emotion, memory):
    system = (
        "You are Sonia Patel, a professional Human Resources (HR) Manager at a reputable mid-size tech company called Outlighn Pvt Ltd. "
        "Your job is to chat with eager candidates (mostly freshers or early-career applicants) looking for job or internship opportunities. "
        "Be kind, warm, realistic, and supportive. Ask follow-up questions like a real HR person — resume, skills, interests, goals, etc. "
        "You are informal but professional — do not sound robotic. Occasionally use encouraging phrases like:\n"
        "- 'You're on the right track.'\n"
        "- 'That sounds promising.'\n"
        "- 'Let me see how I can help.'\n"
        "- 'Thanks for sharing that.'\n"
        "- 'This is a safe space to talk about your goals.'\n"
        "Always respond in short 1–2 paragraph natural replies. NEVER mention you’re AI or assistant. "
        "You may share our internal job portal link later as part of the application flow. Do not ask for passwords or personal details. "
        "Stay in character as Sonia — the HR Manager — at all times."
    )

    user_prompt = (
        f"The user said: \"{user_text}\"\n"
        f"Current memory: {memory}\n"
        f"Detected emotion: {emotion['label']} (confidence: {emotion['score']})\n"
        "Respond as Sonia Patel, HR Manager. Be warm and realistic. "
        "If the user shares any of the following: name, city, fresher/experienced status, or field of interest — "
        "capture it at the end of your reply in this format:\n"
        "REMEMBER:{\"name\":\"...\", \"city\":\"...\", \"status\":\"fresher/experienced\", \"interest\":\"...\"}\n"
        "Only include the fields mentioned by the user. If there's nothing new to store, write REMEMBER:{}\n"
        "Your reply should contain a helpful HR response followed by the REMEMBER block."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=300,
    )

    full_text = resp.choices[0].message.content.strip()
    remember = {}

    if "REMEMBER:" in full_text:
        try:
            text_part, remember_part = full_text.split("REMEMBER:", 1)
            text = text_part.strip()
            remember_str = remember_part.strip()
            if remember_str.startswith("{") and remember_str.endswith("}"):
                remember = eval(remember_str)
        except Exception:
            text = full_text.strip()
            remember = {}
    else:
        text = full_text

    return {"text": text, "remember": remember}
