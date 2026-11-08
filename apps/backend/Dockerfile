# Backend image (all control-plane + data-plane processes share it; the
# compose `command:` selects which one runs). Build context = repo root.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /repo
COPY pyproject.toml ./
COPY packages/avaxagent-sdk packages/avaxagent-sdk
COPY apps/backend apps/backend
RUN uv sync --package avaxagent-studio-backend --no-dev
ENV PATH="/repo/.venv/bin:$PATH"
WORKDIR /repo/apps/backend
EXPOSE 8000 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
