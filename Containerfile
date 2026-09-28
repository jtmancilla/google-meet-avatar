# --- Stage 1: build (install deps, no source code) ---
FROM python:3.10-slim AS builder

# Install uv (fast Python package manager).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy only dependency files first → layer cache stays valid unless deps change.
COPY pyproject.toml uv.lock .python-version ./

# Install production deps (no dev group) into the system Python.
RUN uv sync --frozen --no-dev --no-install-project

# --- Stage 2: runtime (lean, no build tools) ---
FROM python:3.10-slim

WORKDIR /app

# Copy the installed virtualenv from builder.
COPY --from=builder /app/.venv /app/.venv

# Put the venv's Python first on PATH.
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source.
COPY agent.py gate.py notes.py profiles.py ./

# Create the memoria directory (bind-mounted at runtime for persistence).
RUN mkdir -p /app/memoria

# The worker is a long-running process (no HTTP ports needed).
# It connects outbound to LiveKit Cloud via WebSocket.
ENTRYPOINT ["python", "agent.py", "dev"]
