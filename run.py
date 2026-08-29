import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import uvicorn

# Ensure backend directory is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if __name__ == "__main__":
    print("==================================================")
    print("🤖 Starting Larvi Autonomous AI Agent System...")
    print("==================================================")
    print("📍 Dashboard UI: http://localhost:8000")
    print("📍 OpenAPI Docs: http://localhost:8000/docs")
    print("⚡ Default Mode: Sandbox Mode (Instant Mock Execution)")
    print("==================================================")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        app_dir=os.path.join(os.path.dirname(__file__), "backend")
    )
