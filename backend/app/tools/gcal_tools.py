from typing import List, Dict, Any, Optional
from datetime import datetime
from ..schemas.models import CalendarEvent, ToolResult
from .mock_services import mock_store
from ..services.google_auth import google_auth

class GoogleCalendarTools:
    """Tools for Google Calendar Operations (GCal API & Mock Provider)."""

    @staticmethod
    def get_calendar_events(query_date: Optional[str] = None, use_mock: bool = True) -> ToolResult:
        """Fetch list of scheduled events."""
        try:
            if not use_mock and google_auth.is_authenticated():
                service = google_auth.get_calendar_service()
                if service:
                    now = datetime.utcnow().isoformat() + 'Z'
                    events_result = service.events().list(
                        calendarId='primary', timeMin=now,
                        maxResults=10, singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    items = events_result.get('items', [])
                    formatted_items = []
                    for item in items:
                        start = item.get('start', {}).get('dateTime') or item.get('start', {}).get('date', '')
                        end = item.get('end', {}).get('dateTime') or item.get('end', {}).get('date', '')
                        formatted_items.append({
                            "id": item.get('id'),
                            "title": item.get('summary', 'Untitled Event'),
                            "description": item.get('description', ''),
                            "start_time": start,
                            "end_time": end,
                            "location": item.get('location', ''),
                            "attendees": [a.get('email') for a in item.get('attendees', []) if a.get('email')],
                            "status": item.get('status', 'confirmed')
                        })
                    return ToolResult(tool_name="get_calendar_events", success=True, data=formatted_items)

            # Fallback to Sandbox / Mock Data
            events_data = [evt.model_dump() for evt in mock_store.calendar_events if evt.status != "cancelled"]
            return ToolResult(tool_name="get_calendar_events", success=True, data=events_data)
        except Exception as e:
            return ToolResult(tool_name="get_calendar_events", success=False, error=str(e))

    @staticmethod
    def check_availability(start_time: str, end_time: str, use_mock: bool = True) -> ToolResult:
        """Checks for scheduling conflicts in a given time slot."""
        try:
            # Parse requested window
            conflicts = []
            events_res = GoogleCalendarTools.get_calendar_events(use_mock=use_mock)
            if events_res.success and events_res.data:
                for evt in events_res.data:
                    evt_start = evt.get("start_time", "")
                    evt_end = evt.get("end_time", "")
                    # Simple ISO overlap check
                    if (start_time < evt_end and end_time > evt_start):
                        conflicts.append(evt)

            is_available = len(conflicts) == 0
            res = {
                "available": is_available,
                "requested_slot": {"start_time": start_time, "end_time": end_time},
                "conflicts": conflicts
            }
            return ToolResult(tool_name="check_availability", success=True, data=res)
        except Exception as e:
            return ToolResult(tool_name="check_availability", success=False, error=str(e))

    @staticmethod
    def create_calendar_event(
        title: str,
        start_time: str,
        end_time: str,
        description: str = "",
        attendees: Optional[List[str]] = None,
        location: str = "",
        use_mock: bool = True
    ) -> ToolResult:
        """Schedules a new calendar event."""
        try:
            if not use_mock and google_auth.is_authenticated():
                service = google_auth.get_calendar_service()
                if service:
                    event_body = {
                        "summary": title,
                        "description": description,
                        "location": location if location else "Google Meet",
                        "start": {"dateTime": start_time if "T" in start_time else f"{start_time}T09:00:00Z"},
                        "end": {"dateTime": end_time if "T" in end_time else f"{end_time}T10:00:00Z"},
                    }
                    if attendees:
                        event_body["attendees"] = [{"email": a} for a in attendees]

                    created_event = service.events().insert(calendarId="primary", body=event_body).execute()
                    return ToolResult(tool_name="create_calendar_event", success=True, data={
                        "id": created_event.get("id"),
                        "title": created_event.get("summary"),
                        "start_time": created_event.get("start", {}).get("dateTime"),
                        "end_time": created_event.get("end", {}).get("dateTime"),
                        "status": "confirmed_in_gcal"
                    })

            # Mock Store Operation
            new_id = f"evt-{len(mock_store.calendar_events) + 101}"
            attendees_list = attendees if attendees else ["user@techcorp.com"]
            
            new_evt = CalendarEvent(
                id=new_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                location=location if location else "Google Meet",
                attendees=attendees_list,
                status="confirmed"
            )

            mock_store.calendar_events.append(new_evt)
            return ToolResult(tool_name="create_calendar_event", success=True, data=new_evt.model_dump())
        except Exception as e:
            return ToolResult(tool_name="create_calendar_event", success=False, error=str(e))

    @staticmethod
    def cancel_calendar_event(event_id: str, use_mock: bool = True) -> ToolResult:
        """Cancels/deletes a calendar event."""
        try:
            if not use_mock and google_auth.is_authenticated():
                service = google_auth.get_calendar_service()
                if service:
                    service.events().delete(calendarId="primary", eventId=event_id).execute()
                    return ToolResult(tool_name="cancel_calendar_event", success=True, data={"event_id": event_id, "status": "deleted_from_gcal"})

            for evt in mock_store.calendar_events:
                if evt.id == event_id or event_id.lower() in evt.title.lower():
                    evt.status = "cancelled"
                    return ToolResult(tool_name="cancel_calendar_event", success=True, data={"event_id": evt.id, "title": evt.title, "status": "cancelled"})

            return ToolResult(tool_name="cancel_calendar_event", success=False, error=f"Event {event_id} not found")
        except Exception as e:
            return ToolResult(tool_name="cancel_calendar_event", success=False, error=str(e))

gcal_tools = GoogleCalendarTools()
