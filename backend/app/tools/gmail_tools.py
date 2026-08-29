from typing import List, Dict, Any, Optional
import base64
from email.mime.text import MIMEText
from ..schemas.models import EmailMessage, ToolResult
from .mock_services import mock_store
from ..services.google_auth import google_auth

class GmailTools:
    """Tools for Email Operations (Gmail API & Mock Provider)."""

    @staticmethod
    def _build_raw_message(to: str, subject: str, body: str) -> Dict[str, str]:
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw}

    @staticmethod
    def search_emails(query: str = "", use_mock: bool = True) -> ToolResult:
        """Search emails based on natural language query or status."""
        try:
            if not use_mock and google_auth.is_authenticated():
                service = google_auth.get_gmail_service()
                if service:
                    q = query if query else "is:unread"
                    res = service.users().messages().list(userId='me', q=q, maxResults=10).execute()
                    messages = res.get('messages', [])
                    results = []
                    for m in messages:
                        msg_detail = service.users().messages().get(userId='me', id=m['id']).execute()
                        snippet = msg_detail.get('snippet', '')
                        headers = {h['name'].lower(): h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}
                        results.append({
                            "id": m['id'],
                            "thread_id": m.get('threadId', ''),
                            "sender": headers.get('from', ''),
                            "subject": headers.get('subject', 'No Subject'),
                            "snippet": snippet,
                            "date": headers.get('date', '')
                        })
                    return ToolResult(tool_name="search_emails", success=True, data=results)

            # Fallback to Sandbox / Mock Data
            filtered = []
            q_lower = query.lower()
            for msg in mock_store.emails:
                if not q_lower or q_lower in msg.subject.lower() or q_lower in msg.body.lower() or q_lower in msg.sender.lower():
                    filtered.append(msg.model_dump())
            
            return ToolResult(tool_name="search_emails", success=True, data=filtered)
        except Exception as e:
            return ToolResult(tool_name="search_emails", success=False, error=str(e))

    @staticmethod
    def read_email_thread(thread_id: str, use_mock: bool = True) -> ToolResult:
        """Reads full message contents of a specific email thread."""
        try:
            if not use_mock and google_auth.is_authenticated():
                service = google_auth.get_gmail_service()
                if service:
                    thread = service.users().threads().get(userId='me', id=thread_id).execute()
                    return ToolResult(tool_name="read_email_thread", success=True, data=thread)

            # Fallback to Mock Store
            msgs = [m.model_dump() for m in mock_store.emails if m.thread_id == thread_id or m.id == thread_id]
            if msgs:
                return ToolResult(tool_name="read_email_thread", success=True, data=msgs[0])
            
            # Return first email if thread not explicitly matched
            return ToolResult(tool_name="read_email_thread", success=True, data=mock_store.emails[0].model_dump())
        except Exception as e:
            return ToolResult(tool_name="read_email_thread", success=False, error=str(e))

    @staticmethod
    def draft_email(recipient: str, subject: str, body: str, use_mock: bool = True) -> ToolResult:
        """Drafts an email for user review."""
        try:
            if not use_mock and google_auth.is_authenticated():
                service = google_auth.get_gmail_service()
                if service:
                    raw_msg = GmailTools._build_raw_message(recipient, subject, body)
                    draft = service.users().drafts().create(
                        userId="me",
                        body={"message": raw_msg}
                    ).execute()
                    draft_data = {
                        "id": draft.get("id"),
                        "recipient": recipient,
                        "subject": subject,
                        "body": body,
                        "status": "drafted_in_gmail"
                    }
                    return ToolResult(tool_name="draft_email", success=True, data=draft_data)

            # Fallback to Sandbox / Mock Store
            draft_data = {
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "status": "drafted"
            }
            return ToolResult(tool_name="draft_email", success=True, data=draft_data)
        except Exception as e:
            return ToolResult(tool_name="draft_email", success=False, error=str(e))

    @staticmethod
    def send_email(recipient: str, subject: str, body: str, use_mock: bool = True) -> ToolResult:
        """Sends an email to the recipient."""
        try:
            if not use_mock and google_auth.is_authenticated():
                service = google_auth.get_gmail_service()
                if service:
                    raw_msg = GmailTools._build_raw_message(recipient, subject, body)
                    sent = service.users().messages().send(
                        userId="me",
                        body=raw_msg
                    ).execute()
                    sent_record = {
                        "id": sent.get("id"),
                        "recipient": recipient,
                        "subject": subject,
                        "body": body,
                        "timestamp": "Just now",
                        "status": "sent_via_gmail_api"
                    }
                    return ToolResult(tool_name="send_email", success=True, data=sent_record)

            # Mock Store Send Operation
            sent_record = {
                "id": f"sent-{len(mock_store.sent_emails) + 1}",
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "timestamp": "Just now"
            }
            mock_store.sent_emails.append(sent_record)
            return ToolResult(tool_name="send_email", success=True, data=sent_record)
        except Exception as e:
            return ToolResult(tool_name="send_email", success=False, error=str(e))

gmail_tools = GmailTools()
