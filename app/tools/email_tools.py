"""Anthropic tool-use schemas for the Email Agent's capabilities."""

EMAIL_TOOL_SCHEMAS = [
    {
        "name": "search_emails",
        "description": "Search emails using a free-form Gmail query (supports keywords, from:, subject:, is:unread, etc).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query"},
                "max_results": {"type": "integer", "description": "Max results to return", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_recent_emails",
        "description": "Get the most recent emails in the inbox.",
        "input_schema": {
            "type": "object",
            "properties": {"max_results": {"type": "integer", "default": 10}},
        },
    },
    {
        "name": "search_emails_by_sender",
        "description": "Find emails from a specific sender (name or email address).",
        "input_schema": {
            "type": "object",
            "properties": {
                "sender": {"type": "string"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["sender"],
        },
    },
    {
        "name": "search_emails_by_subject",
        "description": "Find emails whose subject line matches a keyword or phrase.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["subject"],
        },
    },
    {
        "name": "read_email",
        "description": "Read the full headers and body of one specific email by its message id. Use this to extract details (e.g. a meeting time) mentioned in the email, or before summarizing it.",
        "input_schema": {
            "type": "object",
            "properties": {"message_id": {"type": "string"}},
            "required": ["message_id"],
        },
    },
    {
        "name": "create_draft",
        "description": "Create a draft email. Safe: does not send anything, no confirmation needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "send_email",
        "description": "Send a brand-new email. IMPORTANT ACTION: only call this after the user has explicitly confirmed the recipient, subject and body.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "reply_email",
        "description": "Reply within an existing email thread by message id. IMPORTANT ACTION: only call this after the user has explicitly confirmed the reply text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["message_id", "body"],
        },
    },
]

EMAIL_TOOL_NAMES = {t["name"] for t in EMAIL_TOOL_SCHEMAS}
