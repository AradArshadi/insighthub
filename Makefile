# Insighthub Makefile

.PHONY: help up down build test migrate shell logs clean

help:
    @echo "Insighthub Development Commands:"
    @echo "  make up          - Start all services"
    @echo "  make down        - Stop all services"
    @echo "  make build       - Rebuild containers"
    @echo "  make test        - Run tests"
    @echo "  make migrate     - Run migrations"
    @echo "  make shell       - Open Django shell"
    @echo "  make logs        - View logs"
    @echo "  make clean       - Clean temporary files"

up:
    docker-compose up -d

down:
    docker-compose down

build:
    docker-compose build --no-cache

rebuild: down build up

test:
    docker-compose exec backend python manage.py test

migrate:
    docker-compose exec backend python manage.py migrate

makemigrations:
    docker-compose exec backend python manage.py makemigrations

shell:
    docker-compose exec backend python manage.py shell_plus

logs:
    docker-compose logs -f backend

clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    find . -type d -name ".pytest_cache" -delete
    rm -rf .coverage htmlcov

# Database
resetdb:
    docker-compose down -v
    docker-compose up -d postgres redis
    sleep 5
    docker-compose exec postgres psql -U insighthub -d insighthub_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    docker-compose up -d

# Frontend (when we add it)
frontend-up:
    cd frontend && npm start

# Monitoring
monitor:
    open http://localhost:3000  # Grafana
    open http://localhost:9090  # Prometheus