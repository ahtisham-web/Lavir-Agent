"""
Thin wrapper around the Gmail API. Every public method returns a plain
dict with a "status" key ("success" | "error") and never raises -
MasterAgent relies on this to know when it's actually safe to tell the
user an operation succeeded.
"""
import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.auth import get_credentials


class GmailService:
    def __init__(self):
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build("gmail", "v1", credentials=get_credentials())
        return self._service

    # ---- helpers ---------------------------------------------------

    def _extract_headers(self, message: dict) -> dict:
        headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
        return {
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
        }

    def _extract_body(self, payload: dict) -> str:
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        for part in payload.get("parts", []) or []:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
        for part in payload.get("parts", []) or []:
            body = self._extract_body(part)
            if body:
                return body
        return ""

    def _build_raw_message(self, to, subject, body, thread_id=None, in_reply_to_header=None):
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if in_reply_to_header:
            message["In-Reply-To"] = in_reply_to_header
            message["References"] = in_reply_to_header
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        payload = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id
        return payload

    # ---- public tool-facing methods --------------------------------

    def search_emails(self, query: str, max_results: int = 10) -> dict:
        try:
            res = self.service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()
            items = res.get("messages", [])
            results = []
            for item in items:
                msg = self.service.users().messages().get(
                    userId="me", id=item["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                ).execute()
                info = self._extract_headers(msg)
                info["id"] = item["id"]
                info["snippet"] = msg.get("snippet", "")
                results.append(info)
            return {"status": "success", "count": len(results), "emails": results}
        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_recent_emails(self, max_results: int = 10) -> dict:
        return self.search_emails("in:inbox", max_results)

    def read_email(self, message_id: str) -> dict:
        try:
            msg = self.service.users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute()
            info = self._extract_headers(msg)
            info["id"] = message_id
            info["thread_id"] = msg.get("threadId")
            info["body"] = self._extract_body(msg.get("payload", {}))
            return {"status": "success", "email": info}
        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def create_draft(self, to: str, subject: str, body: str) -> dict:
        try:
            msg = self._build_raw_message(to, subject, body)
            draft = self.service.users().drafts().create(
                userId="me", body={"message": msg}
            ).execute()
            return {"status": "success", "draft_id": draft.get("id")}
        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_email(self, to: str, subject: str, body: str) -> dict:
        try:
            msg = self._build_raw_message(to, subject, body)
            sent = self.service.users().messages().send(userId="me", body=msg).execute()
            return {"status": "success", "message_id": sent.get("id")}
        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def reply_email(self, message_id: str, body: str) -> dict:
        try:
            original = self.service.users().messages().get(
                userId="me", id=message_id, format="metadata",
                metadataHeaders=["From", "Subject", "Message-ID"],
            ).execute()
            headers = self._extract_headers(original)
            to = headers.get("from", "")
            subject = headers.get("subject", "")
            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"
            msg = self._build_raw_message(to, subject, body, thread_id=original.get("threadId"))
            sent = self.service.users().messages().send(userId="me", body=msg).execute()
            return {"status": "success", "message_id": sent.get("id")}
        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
