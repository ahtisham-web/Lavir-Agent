"""
Shared OAuth2 credential handling for Gmail + Google Calendar.
Uses a single consent flow covering both APIs' scopes so the user only
authenticates once. Tokens are cached to disk (GOOGLE_TOKEN_FILE) and
refreshed automatically; nothing sensitive is hard-coded.
"""
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar",
]


def get_credentials() -> Credentials:
    creds = None
    token_file = settings.GOOGLE_TOKEN_FILE

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Missing {settings.GOOGLE_CREDENTIALS_FILE}. Download an OAuth "
                    "'Desktop app' client from Google Cloud Console and place it here."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.GOOGLE_CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return creds
