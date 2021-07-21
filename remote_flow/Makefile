AWS_CONFIG_PATH := $(HOME)/.aws
METAFLOW_CONFIG_PATH := $(HOME)/.metaflowconfig

DOCKER_TAG := metaflow-intent-prediction
DOCKER_RUN_TAG := $(DOCKER_TAG)-run
DOCKER_UPLOAD_TAG := $(DOCKER_TAG)-upload

DOCKER_ARGS := --env-file .env \
	--env USERNAME=$(USER) \
	--volume $(AWS_CONFIG_PATH):/root/.aws
DOCKER_RUN_ARGS := $(DOCKER_ARGS) \
	--volume $(METAFLOW_CONFIG_PATH):/root/.metaflowconfig
DOCKER_UPLOAD_ARGS := $(DOCKER_ARGS) \
	--volume $(shell pwd)/data:/data \
	--env LOCAL_DATA_PATH=/data


# Step 1: Data upload
upload: upload.build
	docker run --rm $(DOCKER_UPLOAD_ARGS) $(DOCKER_UPLOAD_TAG)

upload.build:
	docker build --file docker/upload/Dockerfile --tag $(DOCKER_UPLOAD_TAG) .

upload.bash: upload.build
	docker run --rm -it $(DOCKER_UPLOAD_ARGS) $(DOCKER_UPLOAD_TAG) /bin/bash


# Step 2: The whole #!
run: run.build
	docker run --rm $(DOCKER_RUN_ARGS) $(DOCKER_RUN_TAG)

run.build:
	docker build --file docker/run/Dockerfile --tag $(DOCKER_RUN_TAG) .

run.bash: run.build
	docker run --rm -it $(DOCKER_RUN_ARGS) $(DOCKER_RUN_TAG) /bin/bash
