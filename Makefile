# export this so that poetry finds itself in the venv and can
# run things from there
export VIRTUAL_ENV = .venv
PYTHON_VERSION ?= python3.8
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
	@echo "  dev-env-up: Spin up postgres and dynamo dependencies locally"
	@echo ""
	@echo "  dev-env-down: Stop local postgres and dynamo dependencies"

install:
	$(POETRY) install
	$(POETRY) run pre-commit install

lint: install
	$(POETRY) run tox -e isort,black,flake8,mypy

test: install
	$(POETRY) run tox

test-in-ci:
	$(POETRY) run tox -e ci

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

	# TODO: Are these still needed?
	rm -rf .make_install_flag
	rm -rf *.egg-info
	rm -f *.tar.gz
	rm -rf tar-source
