ENVIRONMENT ?= dev
VIRTUALENV_PATH ?= venv

DOCKER_IMAGE_PATH ?= sylvanld/blog
DOCKER_IMAGE_TAG ?= dev

DOCKER_IMAGE_NAME ?= $(DOCKER_IMAGE_PATH):$(DOCKER_IMAGE_TAG)

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

$(VIRTUALENV_PATH): # Create virtualenv
	virtualenv -p python3 $(VIRTUALENV_PATH)

requires-venv: # Create virtualenv and install dependencies if needed
	@[ -d "$(VIRTUALENV_PATH)" ] || make install

install: $(VIRTUALENV_PATH) ## Install build/dev dependencies
	$(VIRTUALENV_PATH)/bin/pip install -r requirements/$(ENVIRONMENT).txt

serve: requires-venv ## Start a development server to preview blog
	$(VIRTUALENV_PATH)/bin/mkdocs serve

build: requires-venv ## Build static blog as HTML from markdown
	$(VIRTUALENV_PATH)/bin/mkdocs build

image: ## Build docker image
	docker build -t $(DOCKER_IMAGE_NAME) .

##date +'%Y.%m.%d.%H.%M'
docker-start: ## Run documentation in docker image
	docker run --name blog -d -p 23401:80 $(DOCKER_IMAGE_NAME)
	@echo "Blog is running at http://localhost:23401"

docker-stop: ## Stop documentation
	docker stop blog
	docker rm blog
