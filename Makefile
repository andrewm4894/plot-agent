.PHONY: help install publish test clean run-examples

help:
	@echo "Available targets:"
	@echo "  install          - Set up local development environment"
	@echo "  test             - Run the test suite"
	@echo "  run-examples     - Run example notebooks"
	@echo "  run-example-script - Run the basic example script"
	@echo "  clean            - Clean build artifacts"
	@echo "  publish          - Build and publish to PyPI"

install:
	@echo "Installing plot-agent for local development..."
	@echo "Installing uv if not present..."
	@which uv > /dev/null || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "Installing dependencies with uv..."
	uv sync --extra dev --extra posthog
	@echo "Installing plot-agent in editable mode..."
	uv pip install -e .
	@echo ""
	@echo "✅ Installation complete!"
	@echo "📝 Next steps:"
	@echo "   1. Copy .env.example to .env and configure your API keys"
	@echo "   2. Run 'make test' to verify everything works"
	@echo "   3. Run 'make run-example-script' to try the agent"

publish: clean test
	@echo "Building distribution files..."
	python -m build
	@echo "Uploading to PyPI..."
	twine upload dist/*

test:
	@echo "Running tests..."
	uv run pytest

run-examples:
	@echo "Running example notebooks..."
	uv run python scripts/run_examples.py --max-workers 3

.PHONY: run-examples-debug
run-examples-debug:
	@echo "Running example notebooks with PLOT_AGENT_DEBUG=1..."
	PLOT_AGENT_DEBUG=1 uv run python scripts/run_examples.py --max-workers 3

.PHONY: run-example-script
run-example-script:
	@echo "Running examples/example.py..."
	uv run python examples/example.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf examples/executed/
