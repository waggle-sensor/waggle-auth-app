# Default environment is 'dev'. You can override it by passing `ENV=prod` when running `make`.
ENV ?= dev

# Default value for data file path, can be overridden by passing `DATA_FILE`
DATA_FILE ?= ../waggle-auth-app-fixtures/data.json

# Extract just the filename from the data file path
DATA_FILENAME := $(notdir $(DATA_FILE))

# Set the compose file based on the environment.
DOCKER_COMPOSE_FILE := ./env/$(ENV)/docker-compose.yaml

# If ENV is dev, use --force-recreate to see changes immediately.
ifeq ($(ENV),dev)
FORCE_RECREATE := --force-recreate
else
FORCE_RECREATE :=
endif

start:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) up --build $(FORCE_RECREATE) -d

stop:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) down --volumes --remove-orphans

migrate:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py migrate

collectstatic:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py collectstatic --no-input

createsuperuser:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py createsuperuser

loaddata:
	@cp $(DATA_FILE) ./$(DATA_FILENAME)
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py loaddata $(DATA_FILENAME)
	@rm ./$(DATA_FILENAME)

test:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py test
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec django python manage.py check --deploy

up:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) up --build $(FORCE_RECREATE)

logs:
	@docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f
