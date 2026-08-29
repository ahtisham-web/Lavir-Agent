"""
Calendar Agent: owns all Google Calendar operations, mirroring
EmailAgent's shape so MasterAgent can dispatch to either uniformly.
"""
from app.services.calendar_service import CalendarService
from app.tools.calendar_tools import CALENDAR_TOOL_NAMES


class CalendarAgent:
    TOOL_NAMES = CALENDAR_TOOL_NAMES

    def __init__(self, service=None):
        self.service = service or CalendarService()

    def run_tool(self, name: str, args: dict) -> dict:
        try:
            if name == "get_events":
                return self.service.get_events(args["time_min"], args["time_max"], args.get("max_results", 10))
            if name == "search_events":
                return self.service.search_events(
                    args["query"], args.get("time_min"), args.get("time_max"), args.get("max_results", 10)
                )
            if name == "check_availability":
                return self.service.check_availability(args["start"], args["end"])
            if name == "get_event_details":
                return self.service.get_event_details(args["event_id"])
            if name == "create_event":
                return self.service.create_event(
                    args["summary"], args["start"], args["end"],
                    args.get("description"), args.get("attendees"),
                )
            if name == "update_event":
                return self.service.update_event(
                    args["event_id"], args.get("summary"), args.get("start"),
                    args.get("end"), args.get("description"),
                )
            if name == "reschedule_event":
                return self.service.update_event(args["event_id"], start=args["start"], end=args["end"])
            if name == "cancel_event":
                return self.service.delete_event(args["event_id"])
            return {"status": "error", "error": f"Unknown calendar tool: {name}"}
        except KeyError as e:
            return {"status": "error", "error": f"Missing required argument: {e}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
