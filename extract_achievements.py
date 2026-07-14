import re

file_path = "c:\\Users\\jasil_myg\\Desktop\\OSG-myG-PORTAL-mainnnnn - Copy\\may_june_history.txt"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for conversations and AI messages that seem like summaries
    conversations = re.split(r'============================================================\nCONVERSATION:', content)
    
    summaries = []
    for conv in conversations[1:]:
        lines = conv.split('\n')
        conv_id = lines[0].strip()
        date = lines[1].strip() if len(lines) > 1 else ""
        
        # Extract AI messages
        ai_messages = re.findall(r'AI\s+\[\d+\]:\s*(.*?)(?=\n\s*(?:USER|AI)\s+\[|\Z)', conv, re.DOTALL)
        
        # Filter messages that look like summaries or achievements
        for msg in ai_messages:
            msg_lower = msg.lower()
            if any(keyword in msg_lower for keyword in ['✅', 'summary of', 'successfully', 'implemented', 'fixed', 'built', 'created', 'all done', 'the issue is exactly what i expected', 'the fix:', 'what i did:']):
                if len(msg.split()) > 15: # Ignore very short messages
                    summaries.append(f"Date: {date}\n{msg.strip()[:500]}...\n")
    
    with open("c:\\Users\\jasil_myg\\Desktop\\OSG-myG-PORTAL-mainnnnn - Copy\\summaries.txt", "w", encoding="utf-8") as out:
        out.write("\n---\n".join(summaries))
        
    print(f"Extracted {len(summaries)} potential summaries to summaries.txt")
except Exception as e:
    print(f"Error: {e}")
