import json, os, datetime

brain_dir = r"C:\Users\jasil_myg\.gemini\antigravity-ide\brain"

all_paths = []
for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if f == "transcript.jsonl":
            full = os.path.join(root, f)
            all_paths.append((os.path.getmtime(full), full))

all_paths.sort()
# April, May, June 2026
start_ts = datetime.datetime(2026, 4, 1).timestamp()
end_ts = datetime.datetime(2026, 7, 1).timestamp()

target_paths = [(ts, p) for ts, p in all_paths if start_ts <= ts < end_ts]

output = []
for ts, path in target_paths:
    dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line in lines:
            try:
                obj = json.loads(line)
                typ = obj.get("type", "")
                source = obj.get("source", "")
                
                # Check AI responses for accomplishments
                if typ == "PLANNER_RESPONSE" and source == "MODEL":
                    content = obj.get("content", "")
                    content_lower = content.lower()
                    if any(keyword in content_lower for keyword in ['successfully', 'implemented', 'fixed', 'built', 'created', 'all done', 'the fix:', 'what i did:']):
                        if len(content.split()) > 15:
                            safe = content.encode('ascii', errors='replace').decode('ascii')
                            # Keep it short for the summary text
                            output.append(f"DATE: {dt} | AI: {safe[:300].strip()}...\n")
            except:
                pass

    except Exception as e:
        output.append(f"Error: {e}")

with open("full_ai_achievements.txt", "w", encoding="ascii", errors="replace") as f:
    f.write("\n".join(output))

print(f"Extracted {len(output)} AI achievement notes from {len(target_paths)} conversations.")
