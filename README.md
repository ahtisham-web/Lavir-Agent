# Larvi 🤖 - Autonomous Email & Calendar AI Agent System

Larvi is an autonomous AI agent system designed to understand natural language user requests, coordinate specialized agents (**Email Agent** and **Calendar Agent**), interact with real APIs (**Gmail API** and **Google Calendar API**) or safe sandbox environments, enforce **Human-in-the-Loop (HITL) safety approvals**, and stream real-time execution steps to an interactive modern dashboard.

---

## 🌟 Core Architecture

```
User → Larvi Master Agent → Email Agent / Calendar Agent → Tool or API → HITL Guard → Result → Larvi → User
```

- **Larvi Master Agent**: The central brain parsing user natural-language intent, formulating multi-step execution plans, and delegating tasks.
- **Email Agent**: Understands email threads, extracts meeting dates/times, drafts replies, and prepares outbound emails.
- **Calendar Agent**: Checks free/busy availability slots, identifies scheduling conflicts, and creates or cancels calendar events.
- **Human-in-the-Loop (HITL) Guard**: Intercepts high-stakes actions (sending emails, modifying/deleting calendar events) and pauses the workflow state to request user approval via UI popups.
- **Dual Mode Support**: Seamlessly toggles between **Sandbox (Mock Data)** for instant demonstration and **Real Google OAuth 2.0 API**.

---

## 🚀 Quick Start

### 1. Requirements & Setup
Ensure Python 3.9+ is installed.

```bash
pip install -r backend/requirements.txt
```

### 2. Run Application
Start the FastAPI server & modern interactive dashboard:

```bash
python run.py
```

Open your browser at **`http://localhost:8000`** to access the Larvi Dashboard.

---

## 🧪 Automated Testing

Run the automated agent test suite:

```bash
python -m unittest discover -s tests
```

---

## 🛠️ Key Features & Workflows

1. **Autonomous Inbox-to-Calendar Scheduling**:
   - Prompt: *"Check my recent emails for meeting requests and schedule them on my calendar."*
   - Execution: Email Agent scans inbox -> Master Agent extracts meeting request & proposed time -> Calendar Agent verifies availability -> HITL Safety Guard prompts user for confirmation -> Event booked on Google Calendar.
2. **Real-time Thought & Graph Stream**:
   - Visualizes live execution nodes and agent reasoning graphs via WebSockets.
3. **Interactive Human Safety Guard**:
   - Payload diff preview window allowing explicit **Approve** or **Reject** authorization before any external modification occurs.
