.PHONY: help build up down restart logs clean status

# Default target
help:
	@echo "Available targets:"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - Show logs for all services"
	@echo "  status    - Show status of all services"
	@echo "  clean     - Remove all containers and volumes"
	@echo "  vlm       - Start only VLM server"
	@echo "  robot     - Start only UT Dog server"
	@echo "  simulator - Start only Thor simulator"
	@echo "  memory    - Start only Memory server"
	@echo "  milvus    - Start only Milvus services"

# Build all images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Restart all services
restart: down up

# Show logs
logs:
	docker-compose logs -f

# Show status
status:
	docker-compose ps

# Clean up everything
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Individual services
vlm:
	docker-compose up -d vlm-server

robot:
	docker-compose up -d ut-dog-server

simulator:
	docker-compose up -d thor-simulator

memory:
	docker-compose up -d memory-server

milvus:
	docker-compose up -d milvus etcd minio milvus-server

# Development targets
dev-build:
	docker-compose build --no-cache

dev-logs:
	docker-compose logs -f --tail=100

# Health checks
health:
	@echo "Checking service health..."
	@curl -sf http://localhost:8009/health > /dev/null && echo "✓ VLM Server" || echo "✗ VLM Server"
	@curl -sf http://localhost:3000/health > /dev/null && echo "✓ UT Dog Server" || echo "✗ UT Dog Server"
	@curl -sf http://localhost:3001/health > /dev/null && echo "✓ Thor Simulator" || echo "✗ Thor Simulator"
	@curl -sf http://localhost:8080/health > /dev/null && echo "✓ Memory Server" || echo "✗ Memory Server"
	@curl -sf http://localhost:8000/health > /dev/null && echo "✓ Milvus Server" || echo "✗ Milvus Server" 