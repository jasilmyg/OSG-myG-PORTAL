import json, os, datetime

brain_dir = r"C:\Users\jasil_myg\.gemini\antigravity-ide\brain"

all_paths = []
for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if f == "transcript.jsonl":
            full = os.path.join(root, f)
            all_paths.append((os.path.getmtime(full), full))

all_paths.sort()
cutoff_july = datetime.datetime(2026, 7, 1).timestamp()
may_june_paths = [(ts, p) for ts, p in all_paths if ts < cutoff_july]

output = []
output.append(f"Total May-June conversations: {len(may_june_paths)}\n")

for ts, path in may_june_paths:
    dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    conv_id = path.split("brain\\")[1].split("\\")[0]

    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        first_user = ""
        user_msgs = []

        for line in lines:
            try:
                obj = json.loads(line)
                typ = obj.get("type", "")
                content = obj.get("content", "")
                step = obj.get("step_index", "")

                if typ == "USER_INPUT":
                    start = content.find("<USER_REQUEST>")
                    end = content.find("</USER_REQUEST>")
                    if start >= 0 and end >= 0:
                        msg = content[start+14:end].strip()
                    else:
                        msg = content[:300].strip()
                    if not first_user and msg:
                        first_user = msg[:200]
                    if msg and len(msg) > 5 and msg.lower() not in ["continue", "ok", "yes", "no", "continue."]:
                        user_msgs.append(f"  [{step}] {msg[:250]}")
            except:
                pass

        output.append(f"\n{'='*65}")
        output.append(f"DATE: {dt} | {conv_id[:16]}")
        output.append(f"TOPIC: {first_user[:200]}")
        output.append(f"Steps: {len(lines)} | Meaningful user msgs: {len(user_msgs)}")
        for m in user_msgs:
            # encode to ascii with replacement to avoid errors
            safe = m.encode('ascii', errors='replace').decode('ascii')
            output.append(safe)

    except Exception as e:
        output.append(f"  Error: {e}")

with open("work_history.txt", "w", encoding="ascii", errors="replace") as f:
    f.write("\n".join(output))

print("Done - work_history.txt written")
print(f"Total conversations: {len(may_june_paths)}")
