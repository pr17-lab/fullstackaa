# Dockerfile for the ML sub-service (stateless FastAPI, port 8001)
# Trust model: internal Docker network only — see ml_service/README.md
# Built from ./backend context so it shares requirements.txt with the main app.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/predict/health')" || exit 1

CMD ["uvicorn", "ml_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
