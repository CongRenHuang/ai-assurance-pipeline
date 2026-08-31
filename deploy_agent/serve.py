"""Cloud Run entrypoint: same FastAPI app `adk api_server --with_ui` would
build, plus a /.well-known/agent.json route (WS4-1) that `adk api_server`
has no CLI flag for.

    python -m deploy_agent.serve
"""
from __future__ import annotations
import os
from pathlib import Path

from fastapi.responses import FileResponse
from google.adk.cli.fast_api import get_fast_api_app

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_CARD_PATH = REPO_ROOT / "public" / ".well-known" / "agent.json"

app = get_fast_api_app(agents_dir=str(REPO_ROOT), web=True)


@app.get("/.well-known/agent.json")
async def agent_card():
    return FileResponse(AGENT_CARD_PATH, media_type="application/json")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
