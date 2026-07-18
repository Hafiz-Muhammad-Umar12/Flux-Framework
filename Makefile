.PHONY: install dev test lint format typecheck clean

install:
	pip install -e .

dev:
	pip install -e ".[dev,ollama]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=flux --cov-report=term-missing

lint:
	ruff check flux/ tests/

format:
	ruff format flux/ tests/
	ruff check --fix flux/ tests/

typecheck:
	mypy flux/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .pytest_cache .ruff_cache dist build *.egg-info
