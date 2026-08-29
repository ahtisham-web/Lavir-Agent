"""Anthropic tool-use schemas for the Calendar Agent's capabilities."""

CALENDAR_TOOL_SCHEMAS = [
    {
        "name": "get_events",
        "description": "List calendar events between two ISO 8601 timestamps (e.g. to answer 'what's on my calendar tomorrow').",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_min": {"type": "string", "description": "ISO 8601 start, e.g. 2026-08-25T00:00:00Z"},
                "time_max": {"type": "string", "description": "ISO 8601 end, e.g. 2026-08-25T23:59:59Z"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["time_min", "time_max"],
        },
    },
    {
        "name": "search_events",
        "description": "Search calendar events by keyword (e.g. an attendee name or meeting title), optionally within a time window.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "time_min": {"type": "string"},
                "time_max": {"type": "string"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_availability",
        "description": "Check whether the user is free between two ISO 8601 timestamps, and return any busy periods.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
            "required": ["start", "end"],
        },
    },
    {
        "name": "get_event_details",
        "description": "Get full details of one event by its event id.",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"],
        },
    },
    {
        "name": "create_event",
        "description": "Create a new calendar event. If timing wasn't explicitly confirmed by the user, check availability first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start": {"type": "string", "description": "ISO 8601 datetime"},
                "end": {"type": "string", "description": "ISO 8601 datetime"},
                "description": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["summary", "start", "end"],
        },
    },
    {
        "name": "update_event",
        "description": "Update fields (title/time/description) of an existing event by id. IMPORTANT ACTION for meetings the user cares about: confirm with the user first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "summary": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "reschedule_event",
        "description": "Move an existing event to a new start/end time. IMPORTANT ACTION: only call after the user explicitly confirms the new time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
            "required": ["event_id", "start", "end"],
        },
    },
    {
        "name": "cancel_event",
        "description": "Cancel/delete an existing event by id. IMPORTANT ACTION: only call after the user explicitly confirms.",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"],
        },
    },
]

CALENDAR_TOOL_NAMES = {t["name"] for t in CALENDAR_TOOL_SCHEMAS}
