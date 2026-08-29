from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import json
import asyncio
from typing import Dict, Any

from .schemas.models import UserRequest, AgentResponse, ConfirmationResponse
from .agents.master_agent import master_agent
from .tools.mock_services import mock_store
from .tools.gmail_tools import gmail_tools
from .tools.gcal_tools import gcal_tools
from .services.google_auth import google_auth
from .core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Autonomous Email and Calendar AI Agent System"
)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# Enable CORS & Disable Cache
app.add_middleware(NoCacheMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket Connection Manager for real-time thought streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "authenticated_google": google_auth.is_authenticated(),
        "default_use_mock": settings.DEFAULT_USE_MOCK
    }

@app.get("/api/auth/status")
def get_auth_status():
    return {
        "authenticated": google_auth.is_authenticated(),
        "has_credentials": os.path.exists(settings.GOOGLE_CLIENT_SECRETS_FILE),
        "has_token": os.path.exists(settings.GOOGLE_TOKEN_FILE)
    }

@app.post("/api/auth/login")
def login_google():
    res = google_auth.authenticate_user()
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Authentication failed"))
    return res

@app.post("/api/chat", response_model=AgentResponse)
async def process_chat_request(req: UserRequest):
    """Executes a request through Larvi Master Agent."""
    try:
        response = master_agent.process_request(
            prompt=req.prompt,
            session_id=req.session_id,
            use_mock=req.use_mock
        )
        
        # Broadcast streaming update via WebSocket
        await manager.broadcast({
            "type": "agent_execution",
            "data": response.model_dump()
        })
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/confirm", response_model=AgentResponse)
async def process_confirmation(res: ConfirmationResponse, session_id: str = "default_session", use_mock: bool = True):
    """Processes user Human-in-the-Loop confirmation or rejection."""
    try:
        response = master_agent.resume_with_confirmation(
            session_id=session_id,
            confirmation_res=res,
            use_mock=use_mock
        )
        
        await manager.broadcast({
            "type": "confirmation_processed",
            "data": response.model_dump()
        })
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails")
def get_emails(use_mock: bool = True):
    return gmail_tools.search_emails(use_mock=use_mock)

@app.get("/api/calendar")
def get_calendar(use_mock: bool = True):
    return gcal_tools.get_calendar_events(use_mock=use_mock)

@app.post("/api/reset")
def reset_sandbox():
    mock_store.reset()
    return {"status": "success", "message": "Mock Sandbox reset to default state."}

@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            if req.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mount Frontend Static Directory
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def read_root():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
