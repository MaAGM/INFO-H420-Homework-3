#!/bin/bash
source ~/venv-airflow/bin/activate
export AIRFLOW_HOME=~/airflow-home
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
airflow standalone
