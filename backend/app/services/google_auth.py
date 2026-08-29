import os.path
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from ..core.config import settings

# Google OAuth Scopes for Gmail & Google Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

class GoogleAuthService:
    """Manages Google OAuth 2.0 Credentials and API Service Instances."""
    def __init__(self):
        self.creds: Optional[Credentials] = None
        
    def get_credentials(self, allow_login: bool = False) -> Optional[Credentials]:
        """Loads, refreshes, or optionally initiates interactive login for user credentials."""
        token_file = settings.GOOGLE_TOKEN_FILE
        secrets_file = settings.GOOGLE_CLIENT_SECRETS_FILE

        if os.path.exists(token_file):
            try:
                self.creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            except Exception as e:
                print(f"[GoogleAuth] Token load error: {e}")
                self.creds = None

        # If credentials exist but are expired, attempt refresh
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                with open(token_file, "w") as f:
                    f.write(self.creds.to_json())
            except Exception as e:
                print(f"[GoogleAuth] Token refresh error: {e}")
                self.creds = None

        # If still not valid and login is explicitly allowed, run OAuth consent flow
        if (not self.creds or not self.creds.valid) and allow_login:
            if not os.path.exists(secrets_file):
                print(f"[GoogleAuth] Missing {secrets_file}. Download OAuth desktop client from Google Cloud Console.")
                return None
            try:
                print("[GoogleAuth] Launching local browser OAuth consent server...")
                flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
                self.creds = flow.run_local_server(port=0, prompt="consent")
                with open(token_file, "w") as f:
                    f.write(self.creds.to_json())
                print("[GoogleAuth] Successfully authenticated and saved token.json")
            except Exception as e:
                print(f"[GoogleAuth] OAuth authentication failed: {e}")
                self.creds = None

        return self.creds

    def authenticate_user(self) -> Dict[str, Any]:
        """Triggers interactive browser OAuth login flow."""
        secrets_file = settings.GOOGLE_CLIENT_SECRETS_FILE
        if not os.path.exists(secrets_file):
            return {
                "success": False,
                "error": f"Missing client secrets file '{secrets_file}'. Please place credentials.json in the project root."
            }
        try:
            creds = self.get_credentials(allow_login=True)
            if creds and creds.valid:
                return {"success": True, "message": "Google Account authenticated successfully."}
            else:
                return {"success": False, "error": "Failed to complete Google OAuth authentication flow."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def is_authenticated(self) -> bool:
        creds = self.get_credentials(allow_login=False)
        return creds is not None and creds.valid

    def get_gmail_service(self) -> Optional[Resource]:
        creds = self.get_credentials(allow_login=False)
        if not creds:
            return None
        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            print(f"[GoogleAuth] Failed to build Gmail service: {e}")
            return None

    def get_calendar_service(self) -> Optional[Resource]:
        creds = self.get_credentials(allow_login=False)
        if not creds:
            return None
        try:
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"[GoogleAuth] Failed to build Calendar service: {e}")
            return None

google_auth = GoogleAuthService()
