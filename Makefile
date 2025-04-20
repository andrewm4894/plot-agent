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

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf examples/executed/
