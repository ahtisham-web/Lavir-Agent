from fastapi import FastAPI, HTTPException

from app.agents.master_agent import MasterAgent
from app.state.store import SessionStore
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Larvi", description="Master + Email + Calendar agent system")

master_agent = MasterAgent()
store = SessionStore()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    conversation = store.load(req.session_id)
    try:
        reply = master_agent.handle_message(conversation, req.message)
    except Exception as e:
        # Last-resort safety net so a bug never surfaces as a raw 500 with no context.
        raise HTTPException(status_code=500, detail=f"Larvi failed to process this request: {e}")
    store.save(conversation)

    return ChatResponse(
        session_id=req.session_id,
        reply=reply,
        awaiting_confirmation=bool(conversation.pending_confirmation),
    )
