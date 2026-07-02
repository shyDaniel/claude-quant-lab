FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt ./
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python", "-m", "qlab.briefing_service.main", "serve", "--host", "0.0.0.0", "--port", "8080"]
