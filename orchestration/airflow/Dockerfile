ARG AIRFLOW_VERSION=2.10.5
FROM apache/airflow:${AIRFLOW_VERSION}-python3.11

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /tmp/retailiq-requirements.txt

RUN python -m venv /opt/airflow/retailiq_venv \
    && /opt/airflow/retailiq_venv/bin/python -m pip install --no-cache-dir --upgrade pip setuptools wheel pyproject-hooks \
    && /opt/airflow/retailiq_venv/bin/python -m pip install --no-cache-dir -r /tmp/retailiq-requirements.txt
