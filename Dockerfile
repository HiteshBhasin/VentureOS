# Builds & runs venture-os/agent-engine — the FastAPI API and the worker
# share this image (see fly.toml's [processes]). Fly's GitHub integration
# looks for Dockerfile/fly.toml at the repo root, so the build context here
# is the monorepo root — every COPY below reaches explicitly into
# venture-os/agent-engine/ rather than assuming it.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY venture-os/agent-engine/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY venture-os/agent-engine/ .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
