AWS_CONFIG_PATH := $(HOME)/.aws
METAFLOW_CONFIG_PATH := $(HOME)/.metaflowconfig

DOCKER_TAG := metaflow-intent-prediction
DOCKER_ARGS := --env-file .env \
	--env USERNAME=$(USER) \
	--volume $(AWS_CONFIG_PATH):/root/.aws \
	--volume $(METAFLOW_CONFIG_PATH):/root/.metaflowconfig \
	--volume /var/run/docker.sock:/var/run/docker.sock


build:
	docker build --tag $(DOCKER_TAG) .

start: build
	docker run $(DOCKER_ARGS) $(DOCKER_TAG)

bash: build
	docker run -it --rm $(DOCKER_ARGS) $(DOCKER_TAG) /bin/bash
