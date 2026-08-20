# Build context: the PARENT directory containing both my_agent/ and shared_lib/
#   docker build -f Dockerfile -t my-agent-service ..   (see deploy.sh)
#
# This replaces `adk deploy cloud_run`'s auto-generated Dockerfile, which
# only packages the single agent directory it's pointed at and therefore
# drops sibling packages like shared_lib/.

FROM python:3.11-slim

WORKDIR /app

# Install agent deps first for better layer caching.
COPY my_agent/requirements.txt ./my_agent/requirements.txt
RUN pip install --no-cache-dir -r my_agent/requirements.txt google-adk

# Bring in both the agent package and the shared library it imports from.
COPY my_agent/ ./my_agent/
COPY shared_lib/ ./shared_lib/

# Both my_agent and shared_lib are now top-level packages under /app,
# matching `from shared_lib.policy import evaluate` in my_agent/agent.py.
ENV PYTHONPATH=/app
ENV PORT=8080
EXPOSE 8080

# Adjust to match how you serve the agent locally (adk api_server, or a
# custom FastAPI app built with google.adk.cli.fast_api.get_fast_api_app).
CMD ["adk", "api_server", "--port", "8080", "--host", "0.0.0.0", "my_agent"]
