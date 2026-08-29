from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..schemas.models import EmailMessage, CalendarEvent

class MockDataStore:
    """Stateful Mock Data Store for Sandbox Execution Mode."""
    def __init__(self):
        self.reset()

    def reset(self):
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        next_day_str = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        
        self.emails: List[EmailMessage] = [
            EmailMessage(
                id="msg-101",
                thread_id="thread-101",
                sender="alex.engineer@techcorp.com",
                recipient="user@techcorp.com",
                subject="Sprint Planning Sync & Code Review Request",
                snippet=f"Hey! Can we schedule a 45-min meeting tomorrow ({tomorrow_str}) around 2:00 PM to review Larvi PRs?",
                body=f"Hi team,\n\nI just pushed the initial architecture for Larvi. Can we schedule a 45-minute meeting tomorrow ({tomorrow_str}) at 2:00 PM to review the pull request and discuss API specs?\n\nLet me know if that time works for you!\n\nBest,\nAlex",
                timestamp=f"{today_str}T09:30:00Z",
                unread=True,
                labels=["INBOX", "UNREAD", "IMPORTANT"]
            ),
            EmailMessage(
                id="msg-102",
                thread_id="thread-102",
                sender="sarah.product@techcorp.com",
                recipient="user@techcorp.com",
                subject="Q3 Roadmap Alignment",
                snippet="Hi, please check your calendar for Friday morning for our Q3 planning session.",
                body=f"Hi there,\n\nWe need to finalize the Q3 agent roadmap. I'm proposing a 1-hour session on {next_day_str} at 10:00 AM.\n\nPlease confirm your availability or schedule it on our shared calendar.\n\nThanks,\nSarah",
                timestamp=f"{today_str}T10:15:00Z",
                unread=True,
                labels=["INBOX", "UNREAD"]
            ),
            EmailMessage(
                id="msg-103",
                thread_id="thread-103",
                sender="notifications@calendar.google.com",
                recipient="user@techcorp.com",
                subject="Invitation: Design System Review @ Wed Aug 28, 4pm - 5pm",
                snippet="You have been invited to Design System Review",
                body="Event: Design System Review\nTime: 4:00 PM - 5:00 PM\nOrganizer: UX Team",
                timestamp=f"{today_str}T11:00:00Z",
                unread=False,
                labels=["INBOX"]
            )
        ]
        
        self.calendar_events: List[CalendarEvent] = [
            CalendarEvent(
                id="evt-201",
                title="Daily Engineering Standup",
                description="Daily team sync on active Jira issues.",
                start_time=f"{today_str}T09:00:00",
                end_time=f"{today_str}T09:30:00",
                location="Google Meet (https://meet.google.com/abc-defg-hij)",
                attendees=["alex.engineer@techcorp.com", "sarah.product@techcorp.com", "user@techcorp.com"],
                status="confirmed"
            ),
            CalendarEvent(
                id="evt-202",
                title="Architecture Alignment",
                description="Discussion on state graph management.",
                start_time=f"{tomorrow_str}T11:00:00",
                end_time=f"{tomorrow_str}T12:00:00",
                location="Room 402 / Hybrid",
                attendees=["alex.engineer@techcorp.com", "user@techcorp.com"],
                status="confirmed"
            ),
            CalendarEvent(
                id="evt-203",
                title="Client Support Review",
                description="Monthly support metric check-in.",
                start_time=f"{tomorrow_str}T16:00:00",
                end_time=f"{tomorrow_str}T17:00:00",
                location="Conference Room B",
                attendees=["sarah.product@techcorp.com", "user@techcorp.com"],
                status="confirmed"
            )
        ]
        
        self.sent_emails: List[Dict[str, Any]] = []

mock_store = MockDataStore()
