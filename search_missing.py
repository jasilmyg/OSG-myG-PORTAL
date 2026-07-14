import json, os, datetime

brain_dir = r"C:\Users\jasil_myg\.gemini\antigravity-ide\brain"

all_paths = []
for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if f == "transcript.jsonl":
            full = os.path.join(root, f)
            all_paths.append((os.path.getmtime(full), full))

all_paths.sort()
start_ts = datetime.datetime(2026, 4, 1).timestamp()
end_ts = datetime.datetime(2026, 7, 1).timestamp()

target_paths = [(ts, p) for ts, p in all_paths if start_ts <= ts < end_ts]

found_items = []
for ts, path in target_paths:
    dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line in lines:
            try:
                obj = json.loads(line)
                typ = obj.get("type", "")
                
                # Check for keywords
                if typ in ["USER_INPUT", "PLANNER_RESPONSE"]:
                    content = obj.get("content", "")
                    content_lower = content.lower()
                    if "biggboss" in content_lower or "bigg boss" in content_lower or "fone flix" in content_lower or "foneflix" in content_lower:
                        safe = content.encode('ascii', errors='replace').decode('ascii')
                        found_items.append(f"DATE: {dt} | TYPE: {typ} | MSG: {safe[:800].strip()}...\n")
            except:
                pass

    except Exception as e:
        found_items.append(f"Error: {e}")

with open("missing_projects.txt", "w", encoding="ascii", errors="replace") as f:
    f.write("\n".join(found_items))

print(f"Found {len(found_items)} items related to biggboss / foneflix.")
