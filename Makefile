.PHONY: up down logs test compile import-check config verify

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api worker

test:
