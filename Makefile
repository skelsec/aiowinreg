clean:
	rm -f -r build/
	rm -f -r dist/
	rm -f -r *.egg-info
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +

publish: clean
	python3 sdist bdist_wheel
	python3 -m twine upload dist/*

rebuild: clean
	pip install .

build:
	pip install .