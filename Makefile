# Makefile for local development
.PHONY: help deps run-backend run-dpi build-backend test docker-mindscore docker-up docker-down docker-logs docker-test-mindscore docker-shell docker-clean

help:
	@echo "Targets: deps, run-backend, build-backend, run-dpi, test"
	@echo "Docker targets: docker-mindscore, docker-up, docker-down, docker-logs, docker-test-mindscore, docker-shell, docker-clean"

deps:
	python3 -m pip install --user -r backend/requirements.txt

run-backend:
	# Run the FastAPI backend locally
	uvicorn backend.api.server:app --host 127.0.0.1 --port 8000

build-backend:
	docker build -t jarvis-backend:local -f deployment/docker/Dockerfile.backend .

run-dpi:
	# Assumes jarvis-dpi image exists
	docker run --rm --network host jarvis-dpi:latest

test:
	pytest backend/tests

# Docker targets for MindSpore deployment
docker-mindscore:
	@echo "Building MindSpore Docker image for J.A.R.V.I.S..."
	docker build -f deployment/docker/Dockerfile.mindscore -t jarvis:mindscore .

docker-up:
	@echo "Starting J.A.R.V.I.S. with MindSpore (Docker Compose)..."
	docker-compose -f docker-compose.mindscore.yml up --build

docker-down:
	@echo "Stopping J.A.R.V.I.S. containers..."
	docker-compose -f docker-compose.mindscore.yml down

docker-logs:
	@echo "Viewing J.A.R.V.I.S. logs..."
	docker-compose -f docker-compose.mindscore.yml logs -f mindscore-app

docker-test-mindscore:
	@echo "Testing MindSpore in Docker..."
	docker run --rm mindspore/mindspore:latest-cpu python3 -c \
		"import mindspore; print(f'✅ MindSpore Version: {mindspore.__version__}')"

docker-shell:
	@echo "Opening shell in MindSpore container..."
	docker run -it --rm -v $(pwd):/app mindspore/mindspore:latest-cpu /bin/bash

docker-clean:
	@echo "Cleaning up Docker resources..."
	docker-compose -f docker-compose.mindscore.yml down -v
	docker image rm jarvis:mindscore || true
	docker system prune -f

