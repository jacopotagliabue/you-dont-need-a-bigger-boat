FROM prefecthq/prefect:0.15.1-python3.8

WORKDIR /app

# Node.js dependencies
RUN  apt-get update \
  && apt-get install -y curl --no-install-recommends \
  && curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
  && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*

COPY serverless/package.json serverless/package.json
RUN cd serverless && npm install

# Python dependencies
COPY docker/run/requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Global Configurations
COPY docker/run/dbt_profiles.yml /root/.dbt/profiles.yml
COPY docker/run/great_expectations_config_variables.yml great_expectations/uncommitted/config_variables.yml

# Codebase
COPY . .

# Final envs
ENV METAFLOW_HOME=/root/.metaflowconfig
ENV DBT_PROFILES_DIR=/root/.dbt


CMD [ "python", "./prefect/run_agent.py" ]
