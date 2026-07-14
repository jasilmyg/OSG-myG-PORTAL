import os

file_path = r"C:\Users\jasil_myg\.gemini\antigravity-ide\brain\2d556046-4336-4550-afe9-c59e03f7448f\Detailed_Work_Report_Q2_2026.md"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "## 7. Custom Frontend Projects & Documentation" in line:
        break
    new_lines.append(line)

new_lines.append("## 6. BIGG BOSS & FoneFlix Registration Portals\n")
new_lines.append("Built a highly customized Flask-based web application initially designed for 'Bigg Boss Season 8 – Agnipareeksha' auditions, which was later successfully pivoted into the 'myG FoneFlix Mobile Phone Short Film Contest 2026'.\n\n")
new_lines.append("* **Video Upload Architecture (Google Drive OAuth):**\n")
new_lines.append("  * Engineered a custom OAuth 2.0 Client ID integration that allowed users to authenticate and upload large video files (auditions / short films) directly into their personal Google Drive folders, bypassing the Render server's ephemeral storage limits.\n")
new_lines.append("* **Dynamic UI/UX Design:**\n")
new_lines.append("  * Designed a complex, responsive hero section using precise grid layouts (40/60 split) matching OTT reality-show aesthetics.\n")
new_lines.append("  * Implemented neon-glow typography, dark glassmorphism form backgrounds, and floating 3D particle animations for brand elements.\n")
new_lines.append("* **Project Pivot & Rebranding:**\n")
new_lines.append("  * Successfully transitioned the entire codebase from the Bigg Boss branding (Navy Blue & Neon Pink) to the FoneFlix cinematic branding (Dark Browns & Orange).\n")
new_lines.append("  * Refactored form inputs, consent clauses, and loading UI states to match the new short film contest requirements.\n")

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
