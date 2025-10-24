import json, os
BASE = os.path.join(os.path.dirname(__file__), "..", "data")
MEM_FILE = os.path.join(BASE, "memory.json")
LOG_FILE = os.path.join(BASE, "logs", "chat.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
if not os.path.exists(MEM_FILE):
    with open(MEM_FILE, "w") as f:
        json.dump({}, f)

def load_memory(user_id):
    with open(MEM_FILE, "r") as f:
        mem = json.load(f)
    return mem.get(user_id, {})

def add_memory(user_id, obj):
    with open(MEM_FILE, "r") as f:
        mem = json.load(f)
    mem.setdefault(user_id, {}).update(obj)
    with open(MEM_FILE, "w") as f:
        json.dump(mem, f, indent=2)

def save_message(user_id, sender, text):
    entry = {"user_id":user_id, "sender":sender, "text":text}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry)+"\n")
