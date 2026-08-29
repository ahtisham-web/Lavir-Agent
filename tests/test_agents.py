import unittest
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.schemas.models import StepStatus, ConfirmationResponse
from app.agents.master_agent import master_agent
from app.tools.gmail_tools import gmail_tools
from app.tools.gcal_tools import gcal_tools
from app.tools.mock_services import mock_store

class TestLarviAgentSystem(unittest.TestCase):
    def setUp(self):
        mock_store.reset()

    def test_email_search(self):
        res = gmail_tools.search_emails(query="meeting", use_mock=True)
        self.assertTrue(res.success)
        self.assertGreaterEqual(len(res.data), 1)

    def test_calendar_availability(self):
        res = gcal_tools.check_availability("2026-08-28T14:00:00", "2026-08-28T14:45:00", use_mock=True)
        self.assertTrue(res.success)
        self.assertIn("available", res.data)

    def test_master_agent_email_to_calendar_workflow(self):
        # Run workflow: Scan inbox for meeting request & schedule
        prompt = "Check my recent emails for meeting requests and schedule them on my calendar."
        resp = master_agent.process_request(prompt, session_id="test_session_1", use_mock=True)
        
        # Verify HITL Safety Guard paused action for confirmation
        self.assertEqual(resp.status, StepStatus.REQUIRES_CONFIRMATION)
        self.assertIsNotNone(resp.pending_confirmation)
        self.assertEqual(resp.pending_confirmation.action_type, "create_calendar_event")

        # Simulate user approval
        conf_res = ConfirmationResponse(
            confirmation_id=resp.pending_confirmation.confirmation_id,
            approved=True,
            user_feedback="Approved by unit test"
        )
        resumed_resp = master_agent.resume_with_confirmation("test_session_1", conf_res, use_mock=True)
        self.assertEqual(resumed_resp.status, StepStatus.COMPLETED)
        self.assertIn("Action Confirmed", resumed_resp.final_output)

    def test_master_agent_calendar_query(self):
        prompt = "Do I have any scheduling conflicts tomorrow?"
        resp = master_agent.process_request(prompt, session_id="test_session_2", use_mock=True)
        self.assertEqual(resp.status, StepStatus.COMPLETED)

if __name__ == "__main__":
    unittest.main()
