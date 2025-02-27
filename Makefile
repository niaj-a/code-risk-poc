.PHONY: up down logs test compile import-check config verify

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api worker

test:
	pytest -q

compile:
	python -m compileall app tests

import-check:
	python -c "from app.main import app; print(app.title)"

config:
	docker compose config

# Offline verification suitable for assessment marking (no Docker/LLM/network).
verify: test compile import-check
