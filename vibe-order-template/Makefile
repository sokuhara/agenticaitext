.PHONY: install format lint test check run

install:
	uv sync --all-extras

format:
	uv run ruff format --check .

format-fix:
	uv run ruff format .

lint:
	uv run ruff check .

test:
	uv run pytest

check: format lint test

run:
	uv run uvicorn vibe_order.app:app --reload --port 8000
