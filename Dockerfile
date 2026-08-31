# Fallback path if `adk deploy cloud_run` fails outright.
# python:3.13-slim rather than 3.14: the 3.14 slim image ecosystem may not
# be fully baked yet, and ADK supports 3.10+. Local dev uses 3.14 fine.
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
# deploy_agent/serve.py wraps adk api_server's own FastAPI app (same as
# --with_ui) and adds the /.well-known/agent.json route the CLI has no
# flag for (WS4-1).
CMD ["sh","-c","python -m deploy_agent.serve"]
