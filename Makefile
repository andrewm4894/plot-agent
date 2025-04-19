.PHONY: publish

publish:
	@echo "Building distribution files..."
	python -m build
	@echo "Uploading to PyPI..."
	twine upload dist/*

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
