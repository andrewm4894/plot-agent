.PHONY: publish test clean

publish:
	@echo "Building distribution files..."
	python -m build
	@echo "Uploading to PyPI..."
	twine upload dist/*

test:
	@echo "Running tests..."
	pytest

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
