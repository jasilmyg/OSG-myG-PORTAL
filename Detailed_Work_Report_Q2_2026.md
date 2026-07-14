# Detailed Work Done Report: Q2 2026 (April, May, June)

This document provides an in-depth breakdown of the engineering, database optimization, frontend development, and artificial intelligence integration completed across all workspaces during Q2 2026.

---

## 1. OSG-myG-PORTAL (Claims & WhatsApp Engineering)
Significant architectural work was done to stabilize, enhance, and debug the Onsitego claims management system and its integration with external messaging APIs.

* **WhatsApp API Integration (Telinfy/GreenAds Global):**
  * Engineered automated messaging pipelines linking the portal's events to WhatsApp API endpoints.
  * Debugged payload routing and delivery issues (`whatsapp_debug_log.txt`), ensuring reliable outbound notifications.
  * Rebuilt data fetching logic utilizing Postman API networks (`scrape_postman.py`).
* **Claims Processing & Data Forensics:**
  * Developed targeted investigative scripts (`trace_9895.py`, `investigate_claim.py`, `investigate_data.py`) to trace and resolve specific claim anomalies (e.g., missing follow-ups, stuck statuses).
  * Built and deployed repair utilities (`fix_claims_workflow.py`, `restore_workflow.py`, `fix_status_case.py`) to retroactively fix corrupted claim states.
* **Large-Scale Data Ingestion (OSID):**
  * Engineered massive data parsers for legacy Excel imports (`import_osid_feb2026.py`, `import_osid_feb2026_full.py`).
  * Automated data sanitization pipelines (`fix_date_formats.py`) to standardize European/American date collisions.
* **Google Apps Script Bridge:**
  * Developed `google_apps_script.js` to create a seamless sync between operational Google Sheets and the Django backend, maintaining data integrity across platforms.

---

## 2. Enterprise AI Agent (Loyalty Portal)
Transformed the Loyalty Analytics Portal into an intelligent, conversational Business Intelligence tool by injecting Large Language Models directly into the database querying pipeline.

* **Multi-Layered Agent Architecture:**
  * Built a **SQL Agent** capable of translating natural language business questions into complex PostgreSQL queries.
  * Built an **AI Analyst** layer to interpret the raw database output and generate readable business insights.
* **LLM Integration & Optimization:**
  * Integrated **NVIDIA's API** endpoints to utilize powerful models (like Llama) for code generation.
  * Overcame severe API latency (reducing 5-10 minute wait times to seconds) through aggressive prompt engineering and query scope reduction.
  * Hardened the AI against database schema hallucinations (preventing errors like querying non-existent `future_stores` tables) by explicitly feeding it the database schema context.

---

## 3. Database Administration & Optimization (12.6M+ Rows)
Massive improvements were made to how the Django backend communicates with the DigitalOcean PostgreSQL database, dramatically reducing dashboard load times.

* **Materialized View Overhaul:**
  * Diagnosed a critical cross-join bug in `mv_yearly_cohort` that was duplicating rows and falsely inflating LTV (Lifetime Value) metrics by thousands of percent.
  * Built a robust refresh system (`refresh_mvs.py`) that successfully regenerates all 26 massive materialized views (e.g., `mv_action_engine`, `mv_cohort_customer_years`) concurrently without locking up the database.
* **Caching Infrastructure:**
  * Integrated and configured **Redis** and **LocMemCache** to cache heavy API responses, reducing page load times for 12.6M+ row calculations to milliseconds.
  * Fixed issues where local environments were holding onto stale memory caches.
* **DB Manager Enhancements:**
  * Created custom Python scripts to bypass web-server timeouts when uploading massive `DSR MAY 2026` Excel files.
  * Automated the scrubbing of anomalous data, successfully filtering out internal store transactions (`SMC/EI`, `HEAD OFFICE`) before they corrupted sales analytics.

---

## 4. Machine Learning & Predictive Forecasting
Replaced static dashboard placeholders with live, mathematically rigorous Python forecasting engines.

* **Model Deployment (Scikit-Learn):**
  * Configured and deployed **Random Forest**, **MLPRegressor** (Neural Network proxy), and **GradientBoostingRegressor** models directly into the API endpoint (`CampaignAnalysisAPIView`).
* **Feature Engineering:**
  * Built the highly customized `MalayalamCalendarFeaturizer` to convert dates into multi-dimensional arrays, allowing the AI to factor local Kerala events (like the proximity to *Onam*) into its predictive scoring.
* **Dormant Customer Reactivation System:**
  * Built SQL pre-aggregation engines (`mv_dormant_reactivation`) to accurately bucket customers who purchased in 2024 but went silent in 2025/2026.
  * Designed complex UI visualizers including Plotly **Probability Gauges**, **Semi-Donuts**, and **Dormancy Risk Meters**.

---

## 5. SHE START - Applicant Evaluation Dashboard
Built a complete, isolated dashboard exclusively for managing the "She Start - Her Dreams Start Here" startup program.

* **Live Google Sheets Synchronization:**
  * Utilized the `gspread` library to create a live-syncing engine that perfectly mirrors the applicant Google Sheet to the Django portal every 25 seconds.
* **Advanced Scoring Algorithm:**
  * Programmed a custom mathematical algorithm for 6-panelist scoring: the system automatically identifies and drops the absolute highest (#1) and lowest (#6) scores, then averages the remaining 4 to prevent bias.
* **Interactive Dashboard UI:**
  * Built interactive, inline editing for the `Growth`, `Support Need`, `Emotional`, `Sustainability`, and `Utilization` columns.
  * Engineered a silent saving mechanism to write panelist scores directly to the local Postgres database without page reloads.
  * Implemented an automated badging system that categorizes startups (e.g., *Strong Final Selection* for scores 85+, *Waitlist Consideration*).

---

## 6. Enterprise Retail Dashboard Enhancements
* **High-Speed Reporting:** Swapped out standard `openpyxl` exporters for the Rust-based **`calamine`** engine, drastically accelerating Excel parsing and generation (5-10x faster).
* **DataTables Integration:** Replaced static tables with dynamic, searchable, and sortable DataTables grids.
* **Advanced Metrics:** Integrated complex business logic calculations directly into the Pandas dataframes, including dynamic **Average Selling Price (ASP)** mapping and product-to-category cross-referencing.

---

  * Implemented neon-glow typography, dark glassmorphism form backgrounds, and floating 3D particle animations for brand elements.
* **Project Pivot & Rebranding:**
  * Successfully transitioned the entire codebase from the Bigg Boss branding (Navy Blue & Neon Pink) to the FoneFlix cinematic branding (Dark Browns & Orange).
  * Refactored form inputs, consent clauses, and loading UI states to match the new short film contest requirements.
## 6. BIGG BOSS & FoneFlix Registration Portals
Built a highly customized Flask-based web application initially designed for 'Bigg Boss Season 8 – Agnipareeksha' auditions, which was later successfully pivoted into the 'myG FoneFlix Mobile Phone Short Film Contest 2026'.

* **Video Upload Architecture (Google Drive OAuth):**
  * Engineered a custom OAuth 2.0 Client ID integration that allowed users to authenticate and upload large video files (auditions / short films) directly into their personal Google Drive folders, bypassing the Render server's ephemeral storage limits.
* **Dynamic UI/UX Design:**
  * Designed a complex, responsive hero section using precise grid layouts (40/60 split) matching OTT reality-show aesthetics.
  * Implemented neon-glow typography, dark glassmorphism form backgrounds, and floating 3D particle animations for brand elements.
* **Project Pivot & Rebranding:**
  * Successfully transitioned the entire codebase from the Bigg Boss branding (Navy Blue & Neon Pink) to the FoneFlix cinematic branding (Dark Browns & Orange).
  * Refactored form inputs, consent clauses, and loading UI states to match the new short film contest requirements.
