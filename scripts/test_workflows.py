"""
Demonstration script for the three required multi-step workflows.

Runs against MOCK Gmail/Calendar services (no Google OAuth needed) so it
can be used for grading/demo evidence, while still exercising the real
Master Agent orchestration logic and a real call to the Claude API for
intent understanding + tool selection (requires ANTHROPIC_API_KEY).

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python -m scripts.test_workflows
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.master_agent import MasterAgent
from app.agents.email_agent import EmailAgent
from app.agents.calendar_agent import CalendarAgent
from app.state.conversation import ConversationState


class MockGmailService:
    """In-memory stand-in for GmailService with the same method signatures."""

    def __init__(self):
        self._emails = {
            "msg_ahmed_1": {
                "id": "msg_ahmed_1", "thread_id": "thread_1",
                "from": "Ahmed <ahmed@example.com>", "to": "me@example.com",
                "subject": "Project meeting tomorrow", "date": "Sun, 23 Aug 2026 10:00:00 +0000",
                "body": "Hi, let's meet tomorrow at 3 PM for 1 hour to review the project. - Ahmed",
                "snippet": "Hi, let's meet tomorrow at 3 PM...",
            },
            "msg_ali_1": {
                "id": "msg_ali_1", "thread_id": "thread_2",
                "from": "Ali <ali@example.com>", "to": "me@example.com",
                "subject": "Tomorrow's project meeting", "date": "Sun, 23 Aug 2026 09:00:00 +0000",
                "body": "Reminder: our project meeting is tomorrow at 4 PM for 30 minutes.",
                "snippet": "Reminder: our project meeting is tomorrow at 4 PM...",
            },
        }

    def search_emails(self, query, max_results=10):
        q = query.lower()
        matches = []
        for e in self._emails.values():
            haystack = f"{e['from']} {e['subject']} {e['body']}".lower()
            if any(term.strip(':()') in haystack for term in q.replace("from:", "").replace("subject:", "").split()):
                matches.append({k: e[k] for k in ("id", "from", "to", "subject", "date", "snippet")})
        return {"status": "success", "count": len(matches[:max_results]), "emails": matches[:max_results]}

    def get_recent_emails(self, max_results=10):
        return self.search_emails("", max_results)

    def read_email(self, message_id):
        e = self._emails.get(message_id)
        if not e:
            return {"status": "error", "error": f"No email with id {message_id}"}
        return {"status": "success", "email": e}

    def create_draft(self, to, subject, body):
        return {"status": "success", "draft_id": "draft_mock_1"}

    def send_email(self, to, subject, body):
        return {"status": "success", "message_id": "sent_mock_1"}

    def reply_email(self, message_id, body):
        return {"status": "success", "message_id": "sent_mock_reply_1"}


class MockCalendarService:
    """In-memory stand-in for CalendarService with the same method signatures."""

    def __init__(self):
        self._events = {
            "evt_1": {
                "id": "evt_1", "summary": "Project Review",
                "start": "2026-08-25T15:00:00", "end": "2026-08-25T15:30:00",
                "description": "Weekly review", "attendees": [], "status": "confirmed",
            }
        }
        self._next_id = 2

    def get_events(self, time_min, time_max, max_results=10):
        return {"status": "success", "count": len(self._events), "events": list(self._events.values())[:max_results]}

    def search_events(self, query, time_min=None, time_max=None, max_results=10):
        q = query.lower()
        matches = [e for e in self._events.values() if q in e["summary"].lower()]
        return {"status": "success", "count": len(matches), "events": matches[:max_results]}

    def check_availability(self, start, end):
        busy = [
            {"start": e["start"], "end": e["end"]}
            for e in self._events.values()
            if not (end <= e["start"] or start >= e["end"])
        ]
        return {"status": "success", "free": len(busy) == 0, "busy_periods": busy}

    def get_event_details(self, event_id):
        e = self._events.get(event_id)
        if not e:
            return {"status": "error", "error": f"No event with id {event_id}"}
        return {"status": "success", "event": e}

    def create_event(self, summary, start, end, description=None, attendees=None):
        eid = f"evt_{self._next_id}"
        self._next_id += 1
        e = {
            "id": eid, "summary": summary, "start": start, "end": end,
            "description": description, "attendees": attendees or [], "status": "confirmed",
        }
        self._events[eid] = e
        return {"status": "success", "event": e}

    def update_event(self, event_id, summary=None, start=None, end=None, description=None):
        e = self._events.get(event_id)
        if not e:
            return {"status": "error", "error": f"No event with id {event_id}"}
        if summary is not None:
            e["summary"] = summary
        if start is not None:
            e["start"] = start
        if end is not None:
            e["end"] = end
        if description is not None:
            e["description"] = description
        return {"status": "success", "event": e}

    def delete_event(self, event_id):
        if event_id not in self._events:
            return {"status": "error", "error": f"No event with id {event_id}"}
        del self._events[event_id]
        return {"status": "success", "deleted_event_id": event_id}


def run_turn(master, conversation, label, message):
    print(f"\n--- {label} ---")
    print(f"User: {message}")
    reply = master.handle_message(conversation, message)
    print(f"Larvi: {reply}")
    return reply


def main():
    email_agent = EmailAgent(service=MockGmailService())
    calendar_agent = CalendarAgent(service=MockCalendarService())
    master = MasterAgent(email_agent=email_agent, calendar_agent=calendar_agent)

    # Workflow 1: email -> calendar coordination
    convo1 = ConversationState("demo-workflow-1")
    run_turn(master, convo1, "Workflow 1: Email -> Calendar coordination",
              "Find the email from Ahmed about the project meeting and add that meeting to my calendar.")

    # Workflow 2: context-based follow-up requiring confirmation
    convo2 = ConversationState("demo-workflow-2")
    run_turn(master, convo2, "Workflow 2a: Find a meeting", "Find my meeting with Ali tomorrow.")
    run_turn(master, convo2, "Workflow 2b: Follow-up using context ('it')", "Move it to 5 PM.")
    run_turn(master, convo2, "Workflow 2c: Confirm the sensitive action", "confirm")

    # Workflow 3: the spec's "Advanced Workflow Example"
    convo3 = ConversationState("demo-workflow-3")
    run_turn(
        master, convo3, "Workflow 3: Advanced multi-step (email search -> extract -> availability -> create)",
        "Check whether I received an email from Ali about tomorrow's project meeting. "
        "If you find the meeting time, check whether I am free and add it to my calendar.",
    )


if __name__ == "__main__":
    main()
