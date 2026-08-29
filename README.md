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

     
## Step-by-Step Guide: Generating Google OAuth Credentials

1. **Create or Select a Project**
Go to the Google Cloud Console.

Click on the project dropdown in the top-left menu (next to the Google Cloud logo).

Click New Project, name it Larvi-Agent, and click Create.

2. **Enable Required APIs**
In the top search bar, search for Gmail API and click Enable.

Search for Google Calendar API and click Enable.

3. **Configure the OAuth Consent Screen**
Navigate to APIs & Services > OAuth consent screen in the left sidebar.

Select External as the User Type and click Create.

Fill in basic details:

App name: Larvi Master Agent

User support email: Your Gmail address

Developer contact information: Your Gmail address

Click Save and Continue through Scopes (you can skip adding manual scopes here as your Python code requests them).

Crucial Step — Add Test Users:

On the Test users tab, click + ADD USERS.

Enter your personal Gmail address.

Click Save.

4. **Create Desktop OAuth Credentials**
Go to APIs & Services > Credentials in the left menu.

Click + CREATE CREDENTIALS at the top and select OAuth client ID.

Under Application type, select Desktop app.

Set the Name to:

Larvi Desktop Client

Click Create.

5. **Download and Rename the JSON File**
A popup window titled OAuth client created will appear.

Click DOWNLOAD JSON.

Move the downloaded file into the root directory of your project folder (F:\lavir project\).

Rename the downloaded file to exactly:

**credentials.json**
