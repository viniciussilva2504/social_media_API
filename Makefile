.PHONY: build run stop shell test migrations migrate clean lint format-py check help superuser

help:
	@echo "Available commands:"
	@echo "  make build       - Build Docker image"
	@echo "  make run         - Start containers with docker-compose"
	@echo "  make stop        - Stop running containers"
	@echo "  make shell       - Access web container shell"
	@echo "  make test        - Run tests"
	@echo "  make migrations  - Create Django migrations"
	@echo "  make migrate     - Apply Django migrations"
	@echo "  make superuser   - Create Django superuser"
	@echo "  make clean       - Remove containers and images"
	@echo "  make lint        - Run code linting"
	@echo "  make format-py   - Format code with black"

build:
	docker compose build

run:
	docker compose up -d

stop:
	docker compose down

shell:
	docker compose exec web /bin/bash

test:
	docker compose exec web python manage.py test

migrations:
	docker compose exec web python manage.py makemigrations

migrate:
	docker compose exec web python manage.py migrate

superuser:
	docker compose exec web python manage.py createsuperuser

clean: stop
	docker compose down -v --rmi all

lint:
	flake8 . || true

format-py:
	black . || true

check:
	flake8 .
