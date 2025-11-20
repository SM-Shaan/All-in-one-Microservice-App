.PHONY: install infra-up infra-down dev test lint format migrate seed build clean

install:
	pip install poetry
	poetry install

infra-up:
	docker-compose up -d postgres mongodb redis kafka zookeeper kafka-ui

infra-down:
	docker-compose down -v

dev:
	docker-compose up --build

test:
	pytest -v --cov=app --cov-report=html

lint:
	ruff check .
	black --check .
	mypy .

format:
	black .
	ruff check --fix .

migrate:
	@for service in services/*/; do \
		echo "Migrating $$service"; \
		cd $$service && alembic upgrade head && cd ../..; \
	done

seed:
	python scripts/seed.py

build:
	docker-compose build

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --rmi all
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
