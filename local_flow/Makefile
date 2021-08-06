include .env

SHELL := /bin/bash
DOTENV := set -a && source ./.env && set +a &&

# Defaults values, can be overwritten:
# - by setting the new value on your .env file, eg `MAX_WORKERS=4`
# - or by exporting the variable before the `make` command, eg: `MAX_WORKERS=4 make run`
MAX_WORKERS ?= 8


upload:
	${DOTENV} python local_dataset_upload.py

run:
	${DOTENV} python src/cart_baseline_flow.py --no-pylint run --max-workers ${MAX_WORKERS}

deploy:
	${DOTENV} cd serverless && serverless deploy
