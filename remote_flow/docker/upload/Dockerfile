FROM python:3.8-slim

WORKDIR /app

# Python dependencies
COPY docker/upload/requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY metaflow/data_processing .

# Final envs
ENV LOCAL_DATA_PATH=/data


CMD [ "python", "push_data_to_sf.py" ]
