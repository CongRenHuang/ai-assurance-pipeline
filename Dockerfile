# Fallback path if `adk deploy cloud_run` fails outright.
# python:3.13-slim rather than 3.14: the 3.14 slim image ecosystem may not
# be fully baked yet, and ADK supports 3.10+. Local dev uses 3.14 fine.
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
CMD ["sh","-c","adk api_server deploy_agent --host 0.0.0.0 --port $PORT"]
