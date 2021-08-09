SHELL := /bin/bash
WITH_ENV := set -a && source ./.env && set +a &&


include .env


upload:
	${WITH_ENV} python local_dataset_upload.py

run:
	${WITH_ENV} python src/cart_baseline_flow.py --no-pylint run --max-workers 8

deploy:
	${WITH_ENV} cd serverless && serverless deploy
