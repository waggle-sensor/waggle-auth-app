# Default environment is 'dev'. You can override it by passing `ENV=prod` when running `make`.
ENV ?= dev

# Default value for data file path, can be overridden by passing `DATA_FILE`
DATA_FILE ?= ../waggle-auth-app-fixtures/data.json

# Set the compose file based on the environment.
DOCKER_COMPOSE_FILE := ./env/$(ENV)/docker-compose.yaml

start:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) up --build -d

stop:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) down --volumes --remove-orphans

migrate:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py migrate

collectstatic:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py collectstatic --no-input

createsuperuser:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py createsuperuser

loaddata:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py loaddata $(DATA_FILE)

test:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py test
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py check --deploy

logs:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f
