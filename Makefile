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
	python scripts/run_examples.py --max-workers 3

.PHONY: run-examples-debug
run-examples-debug:
	@echo "Running example notebooks with PLOT_AGENT_DEBUG=1..."
	PLOT_AGENT_DEBUG=1 python scripts/run_examples.py --max-workers 3

.PHONY: run-example-script
run-example-script:
	@echo "Running examples/example.py..."
	python examples/example.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf examples/executed/
