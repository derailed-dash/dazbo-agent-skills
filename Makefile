.DEFAULT_GOAL := help

.PHONY: help install lint lint-fix fix test check clean

help: ## Show available targets and descriptions
	@awk 'BEGIN {FS = ":.*## "; printf "\nAvailable targets:\n"} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python development and test dependencies with uv
	uv sync --dev

lint: ## Run read-only spelling, Ruff lint/format, and Pyright type checks
	uv run codespell -s
	uv run ruff check --diff .
	uv run ruff format --check --diff .
	uv run pyright

lint-fix: ## Apply codespell and Ruff lint/format auto-fixes
	uv run codespell -w
	uv run ruff check --fix .
	uv run ruff format .

fix: lint-fix ## Alias for lint-fix

test: ## Run offline unit test suite
	uv run pytest tests/unit

check: lint test ## Run full offline static and unit test gate

clean: ## Remove local lint and test caches
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
