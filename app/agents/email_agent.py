"""
Email Agent: owns all Gmail-related operations. MasterAgent never talks
to GmailService directly - it always goes through here, which keeps the
tool-execution logic testable and swappable (see scripts/test_workflows.py
for a version that injects a mock service instead of hitting real Gmail).
"""
from app.services.gmail_service import GmailService
from app.tools.email_tools import EMAIL_TOOL_NAMES


class EmailAgent:
    TOOL_NAMES = EMAIL_TOOL_NAMES

    def __init__(self, service=None):
        self.service = service or GmailService()

    def run_tool(self, name: str, args: dict) -> dict:
        try:
            if name == "search_emails":
                return self.service.search_emails(args["query"], args.get("max_results", 10))
            if name == "get_recent_emails":
                return self.service.get_recent_emails(args.get("max_results", 10))
            if name == "search_emails_by_sender":
                return self.service.search_emails(f"from:{args['sender']}", args.get("max_results", 10))
            if name == "search_emails_by_subject":
                return self.service.search_emails(f"subject:({args['subject']})", args.get("max_results", 10))
            if name == "read_email":
                return self.service.read_email(args["message_id"])
            if name == "create_draft":
                return self.service.create_draft(args["to"], args["subject"], args["body"])
            if name == "send_email":
                return self.service.send_email(args["to"], args["subject"], args["body"])
            if name == "reply_email":
                return self.service.reply_email(args["message_id"], args["body"])
            return {"status": "error", "error": f"Unknown email tool: {name}"}
        except KeyError as e:
            return {"status": "error", "error": f"Missing required argument: {e}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
