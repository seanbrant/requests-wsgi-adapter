develop:
	pip install -e .
	pip install "file://`pwd`#egg=wsgiadapter[tests]"

lint:
	@echo "Linting Python files"
	# flake8 is not Python 2.6 compatible and Travis runs this anyway for the
	# rest of Python versions
	python -c "import sys; sys.exit(0 if sys.version_info >= (2,7) else 1)" && flake8 --ignore=E501,E225,E121,E123,E124,E125,E127,E128 wsgiadapter.py || echo "not linting on python 2.6"
	@echo ""

test-python:
	@echo "Running Python tests"
	python setup.py -q test || exit 1
	@echo ""

test: develop lint test-python
