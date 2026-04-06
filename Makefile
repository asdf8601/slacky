.PHONY: dev test lint format

dev:
	uv sync

test:
	uv run pytest -vra

lint:
	uv run ruff check . && uv run ruff format --check .

format:
	uv run ruff format . && uv run ruff check . --fix
