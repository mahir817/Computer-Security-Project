# Agent Security Monitor: Codebase Explanation

This document provides a comprehensive overview of the **Agent Security Monitor** project. It is designed to help team members, as well as faculty reviewing the project, quickly understand the architecture, the purpose of each file, and how the various components interact.

## 1. Project Goal
The core objective of this project is to run an AI agent capable of using tools, while simultaneously monitoring its behavior in real time to prevent and detect unauthorized actions (like Prompt Injection leading to data exfiltration). 

## 2. Core Components Overview

### **The Agent Framework**
- **`agent.py`**: The heart of the AI agent. It contains the `run_agent` loop which executes a ReAct (Reason + Act) loop using an OpenAI-compatible API (e.g., Groq, Gemini). The agent receives a system prompt, reasons about the user's request, and automatically calls tools. It also contains the `SUPPORT_AGENT_PROMPT` which outlines the allowed behavior.
- **`tools.py`**: The tool registry that defines what the agent is capable of doing. This includes functions like `read_ticket`, `search_kb`, `query_db`, and `http_post`. 
  - *Recent Update*: This file previously relied on mock data, but has now been upgraded to interact with a **real database** (`real_data.db`) via `sqlite3`, and make **real network calls** using the `requests` library.

### **The Security & Monitoring Engine**
- **`profiles/support_agent.yaml`**: The behavioral profile for the agent. It strictly defines what tools the agent is allowed to use, which targets (like specific database tables) are permitted, and safe sequence rules.
- **`detector.py`**: The rule-based monitoring engine. For every action the agent attempts, `detector.py` validates it against the YAML profile. It is responsible for detecting:
  - **Scope Abuse:** The agent tries to use a forbidden tool or access a forbidden table (e.g., trying to query the `payroll` table).
  - **Sequence Abuse:** The agent executes tools in a suspicious order (e.g., querying data and immediately making an HTTP POST request).
  - **Rate Abuse:** The agent calls a tool too many times in a short window.
- **`alerter.py`**: Receives anomalies flagged by `detector.py` and logs them as permanent alerts into an SQLite database (e.g., `alerts.db`).
- **`logger.py`**: The central nervous system for auditing. It records every step the agent takes—including its internal thinking and exact tool parameters—into an event database (`events.db`).

### **Data Storage**
- **`setup_db.py`**: A Python script created to initialize the real data environment.
- **`real_data.db`**: A live SQLite database file created by `setup_db.py`. It holds actual relational tables (`tickets`, `kb_index`, `users`, `payroll`, `credentials`) that the agent queries via `tools.py`.
- **`database_dump.sql`**: An exported SQL file of `real_data.db` to quickly review the database schema and inserted rows.

### **User Interface**
- **`dashboard.py`**: An interactive Streamlit web dashboard. It reads from the SQLite databases to provide a real-time administrative view of the agent's behavior, showing live event streams, alert feeds, and security profile inspections. Run it via `streamlit run dashboard.py`.

### **Demonstration Scripts**
To demonstrate the project in action, several entry points are provided:
- **`demo_live_agent.py`**: Runs the live AI agent interacting with the newly updated real database. It runs a normal prompt and a malicious prompt to show how the detector flags unauthorized behavior.
- **`demo_attack.py`, `demo_benign.py`, `demo_rate_abuse.py`**: Scripts demonstrating specific simulated scenarios for testing the monitoring logic.

---

## 3. How to Respond to Common Faculty Update Requests

During a review, your faculty might ask you to make changes to demonstrate your understanding of the codebase. Here is how you would handle common requests:

### **"Add a new tool for the agent"**
1. Open `tools.py`.
2. Write the Python function for the new tool (e.g., `def restart_server(server_id: str):`).
3. Add the function to the `TOOL_FUNCTIONS` dictionary.
4. Add the OpenAI-formatted schema to the `TOOL_SCHEMAS` list so the LLM knows how to call it.
5. Update `profiles/support_agent.yaml` to include the new tool in the `allowed_tools` list, otherwise the `detector.py` will flag it as Scope Abuse.

### **"Change the agent to use a different database"**
1. Open `tools.py`.
2. Update the `sqlite3.connect(DB_PATH)` lines inside `query_db`, `read_ticket`, etc., to use standard connection libraries for the new database (e.g., `psycopg2` for PostgreSQL).
3. The rest of the architecture (Agent, Detector, Logger) remains completely agnostic to the database being used.

### **"Update the security policies / Add a new rule"**
1. If the faculty asks to allow access to a previously blocked table (e.g., allowing access to the `credentials` table), you only need to modify `profiles/support_agent.yaml` and add `credentials` to the `allowed_targets` for `query_db`.
2. If they ask for a completely new type of detection logic (e.g., checking if the agent is sending sensitive keywords via `http_post`), you would update the `_check_scope` or create a new `_check_data_leakage` function inside `detector.py`.

### **"Change the Large Language Model being used"**
1. The project uses the `openai` Python package, which supports many modern LLM providers.
2. In `.env`, you can update `MODEL=...` to use a different model (e.g., `gpt-4`, `llama3-70b`, `gemini-1.5-pro`).
3. Update `API_BASE_URL` in `.env` if you are switching providers (e.g., moving from Groq to OpenAI). The connection is handled seamlessly in `agent.py -> _get_client()`.
