import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_TOKEN_FILE: str = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

    LARVI_DB_PATH: str = os.getenv("LARVI_DB_PATH", "larvi_state.db")

    MAX_AGENT_LOOP_STEPS: int = int(os.getenv("MAX_AGENT_LOOP_STEPS", "8"))


settings = Settings()
