.PHONY: publish test clean run-examples

publish: clean test
	@echo "Building distribution files..."
	python -m build
	@echo "Uploading to PyPI..."
	twine upload dist/*

test:
	@echo "Running tests..."
	pytest

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

# Vibe Plotter App Commands
.PHONY: app app-dev app-install

app:
	@echo "Starting Vibe Plotter app..."
	uv run python -m vibe_plotter.app

app-dev:
	@echo "Starting Vibe Plotter app in development mode with auto-reload..."
	uv run uvicorn vibe_plotter.app:app --reload --host 0.0.0.0 --port 8000

app-install:
	@echo "Installing vibe_plotter dependencies..."
	uv add python-fasthtml monsterui uvicorn pandas numpy plotly kaleido ucimlrepo httpx posthog langchain-core langchain langchain-openai langgraph python-dotenv pydantic matplotlib
