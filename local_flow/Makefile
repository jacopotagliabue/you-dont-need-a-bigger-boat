include .env

SHELL := /bin/bash
DOTENV := set -a && source ./.env && set +a &&

# Defaults values, can be overwritten:
# - by setting the new value on your .env file, eg `METAFLOW_MAX_WORKERS=4`
# - or by exporting the variable before the `make` command, eg: `METAFLOW_MAX_WORKERS=4 make run`
METAFLOW_MAX_WORKERS ?= 8
AWS_DEFAULT_REGION ?= us-west-2
SLS_STAGE ?= STAGE


upload:
	${DOTENV} python local_dataset_upload.py

run:
	${DOTENV} python src/cart_baseline_flow.py --no-pylint run --max-workers ${METAFLOW_MAX_WORKERS}

deploy:
	${DOTENV} cd serverless && serverless deploy
