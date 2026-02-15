# Stratagem — Stackelberg security games
# Run `just` to see all available recipes.

set dotenv-load := false

python := ".venv/bin/python"
pip := ".venv/bin/pip"

# List recipes
default:
    @just --list

# A fresh checkout needs a virtualenv and both Python and Node dependencies.

# Create venv and install all deps (core + web + dev)
setup:
    python3 -m venv .venv
    {{ pip }} install -e ".[web,dev]"
    cd frontend && npm install

# Install backend deps only
install-backend:
    {{ pip }} install -e ".[web,dev]"

# Install frontend deps only
install-frontend:
    cd frontend && npm install

# During development the backend and frontend run as separate processes.
# `just dev` launches both; the individual recipes are useful for debugging.

# Start the FastAPI backend on port 8000
backend *args="":
    {{ python }} -m uvicorn stratagem.web.app:app --host 127.0.0.1 --port 8000 --reload {{ args }}

# Start the Vite dev server on port 5173
frontend:
    cd frontend && npm run dev

# Start both backend and frontend (requires two terminals — use `just dev`)
dev:
    #!/usr/bin/env bash
    trap 'kill 0' EXIT
    just backend &
    just frontend &
    wait

# Linting, formatting, type-checking, and tests — `just ci` runs them all.

# Run the full test suite
test *args="":
    {{ python }} -m pytest tests/ {{ args }}

# Run tests in verbose mode
test-v:
    {{ python }} -m pytest tests/ -v

# Lint with ruff
lint:
    {{ python }} -m ruff check src/ tests/

# Format with ruff
fmt:
    {{ python }} -m ruff format src/ tests/

# Lint + format
check: lint
    {{ python }} -m ruff format --check src/ tests/

# TypeScript type-check
typecheck:
    cd frontend && npx tsc -b

# Build frontend for production
build-frontend:
    cd frontend && npm run build

# Run all checks (lint, tests, typecheck)
ci: check test typecheck

# Convenience wrappers around the CLI and API for quick manual testing.

# Launch the dashboard via the CLI entrypoint
dashboard *args="":
    {{ python }} -m stratagem.cli dashboard {{ args }}

# Solve SSE for a topology via curl (backend must be running)
solve topology="small" budget="5.0":
    curl -s -X POST http://127.0.0.1:8000/api/solve \
        -H 'Content-Type: application/json' \
        -d '{"topology":"{{ topology }}","budget":{{ budget }},"alpha":1.0,"beta":1.0}' \
        | python3 -m json.tool

# List topologies via the API (backend must be running)
topologies:
    curl -s http://127.0.0.1:8000/api/topologies | python3 -m json.tool

# Clean build artifacts
clean:
    rm -rf frontend/dist frontend/node_modules/.vite
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
