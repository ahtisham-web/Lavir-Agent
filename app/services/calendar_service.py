"""
Thin wrapper around the Google Calendar API. Same contract as
GmailService: always returns {"status": "success"|"error", ...}, never
raises up to the agent layer.
"""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.auth import get_credentials


class CalendarService:
    def __init__(self, calendar_id: str = "primary"):
        self._service = None
        self.calendar_id = calendar_id

    @property
    def service(self):
        if self._service is None:
            self._service = build("calendar", "v3", credentials=get_credentials())
        return self._service

    def _simplify(self, e: dict) -> dict:
        return {
            "id": e.get("id"),
            "summary": e.get("summary"),
            "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
            "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
            "description": e.get("description"),
            "attendees": [a.get("email") for a in e.get("attendees", [])] if e.get("attendees") else [],
            "status": e.get("status"),
        }

    def get_events(self, time_min: str, time_max: str, max_results: int = 10) -> dict:
        try:
            res = self.service.events().list(
                calendarId=self.calendar_id, timeMin=time_min, timeMax=time_max,
                maxResults=max_results, singleEvents=True, orderBy="startTime",
            ).execute()
            events = [self._simplify(e) for e in res.get("items", [])]
            return {"status": "success", "count": len(events), "events": events}
        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def search_events(self, query: str, time_min: str = None, time_max: str = None, max_results: int = 10) -> dict:
        try:
            kwargs = {
                "calendarId": self.calendar_id, "q": query, "maxResults": max_results,
                "singleEvents": True, "orderBy": "startTime",
            }
            if time_min:
                kwargs["timeMin"] = time_min
            if time_max:
                kwargs["timeMax"] = time_max
            res = self.service.events().list(**kwargs).execute()
            events = [self._simplify(e) for e in res.get("items", [])]
            return {"status": "success", "count": len(events), "events": events}
        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def check_availability(self, start: str, end: str) -> dict:
        try:
            body = {"timeMin": start, "timeMax": end, "items": [{"id": self.calendar_id}]}
            res = self.service.freebusy().query(body=body).execute()
            busy = res["calendars"][self.calendar_id]["busy"]
            return {"status": "success", "free": len(busy) == 0, "busy_periods": busy}
        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_event_details(self, event_id: str) -> dict:
        try:
            e = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
            return {"status": "success", "event": self._simplify(e)}
        except HttpError as ex:
            return {"status": "error", "error": str(ex)}
        except Exception as ex:
            return {"status": "error", "error": str(ex)}

    def create_event(self, summary: str, start: str, end: str, description: str = None, attendees: list = None) -> dict:
        try:
            body = {"summary": summary, "start": {"dateTime": start}, "end": {"dateTime": end}}
            if description:
                body["description"] = description
            if attendees:
                body["attendees"] = [{"email": a} for a in attendees]
            e = self.service.events().insert(calendarId=self.calendar_id, body=body).execute()
            return {"status": "success", "event": self._simplify(e)}
        except HttpError as ex:
            return {"status": "error", "error": str(ex)}
        except Exception as ex:
            return {"status": "error", "error": str(ex)}

    def update_event(self, event_id: str, summary: str = None, start: str = None, end: str = None, description: str = None) -> dict:
        try:
            event = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
            if summary is not None:
                event["summary"] = summary
            if start is not None:
                event["start"] = {"dateTime": start}
            if end is not None:
                event["end"] = {"dateTime": end}
            if description is not None:
                event["description"] = description
            updated = self.service.events().update(
                calendarId=self.calendar_id, eventId=event_id, body=event
            ).execute()
            return {"status": "success", "event": self._simplify(updated)}
        except HttpError as ex:
            return {"status": "error", "error": str(ex)}
        except Exception as ex:
            return {"status": "error", "error": str(ex)}

    def delete_event(self, event_id: str) -> dict:
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            return {"status": "success", "deleted_event_id": event_id}
        except HttpError as ex:
            return {"status": "error", "error": str(ex)}
        except Exception as ex:
            return {"status": "error", "error": str(ex)}
