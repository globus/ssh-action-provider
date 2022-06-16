# export this so that poetry finds itself in the venv and can
# run things from there
export VIRTUAL_ENV = .venv
PYTHON_VERSION ?= python3.7
POETRY ?= poetry

.PHONY: clean dev-env-down dev-env-up help image install lint test test-in-ci

help:
	@echo "These are our make targets and what they do."
	@echo ""
	@echo "  help:      Show this helptext"
	@echo ""
	@echo "  install:   Setup repo, install build dependencies"
	@echo "             touch a flagfile used by other make targets"
	@echo ""
	@echo "  test:      [install] + [lint] and run the full suite of tests"
	@echo ""
	@echo "  lint:      [install] and lint code with flake8"
	@echo ""
	@echo "  clean:     Typical cleanup, also scrubs venv"
	@echo ""
	@echo "  dev-env-up: Spin up required dependencies locally"
	@echo ""
	@echo "  dev-env-down: Stop running uependencies locally"

install:
	$(POETRY) install
	$(POETRY) run pre-commit install

lint:
	$(POETRY) run tox -e isort,black,flake8,mypy

test:
	$(POETRY) run pytest tests/

dev-env-up:
	docker-compose -f scripts/docker-compose.yml -p automate up -d

dev-env-down:
	docker-compose -f scripts/docker-compose.yml -p automate down

image:
	PROJECT_VERSION=$(shell poetry version -s); \
	docker build -t actions:$$PROJECT_VERSION $(DOCKER_FLAGS) .

clean:
	rm -rf $(VIRTUAL_ENV)
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf .tox/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -name "*.pyc" -delete

