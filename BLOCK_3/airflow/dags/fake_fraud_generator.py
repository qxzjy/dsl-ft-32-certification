# IMPORT
import pandas as pd
import os
from airflow import DAG
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from numpy import random

def _transform_data(**context):
    # Create a file name
    csv_filename = "fake_fraud.csv"

    # Load data from CSV
    data = pd.read_csv(f"{os.getcwd()}/data/{csv_filename}")
    data = data.sample(1)

    # Keeping only relevant data for our model
    data["trans_date_trans_time"] = datetime.now()

    # Put the transformed file in the temp directory
    data.to_csv(f"/tmp/{csv_filename}", index=False)

    # Push the filename to the context to use it later
    context["task_instance"].xcom_push(key="csv_filename", value=csv_filename)


def _load_data(**context):
    # Filename from the context
    csv_filename = context["task_instance"].xcom_pull(key="csv_filename")

    # Load data from CSV
    data= pd.read_csv(f"/tmp/{csv_filename}")
    
    # Connect to PostgreSQL and load data
    postgres_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = postgres_hook.get_sqlalchemy_engine()
    data.to_sql(name=Variable.get("TABLE_FRAUD"), con=engine, index=False, if_exists="append")


# schedule_interval='*/2 * * * *'
with DAG(dag_id="fake_fraud_generator", start_date=datetime(2025, 8, 28), schedule_interval=None, catchup=False) as dag:
    start = DummyOperator(task_id="start")

    transform_data = PythonOperator(
        task_id="transform_data",
        python_callable=_transform_data
    )

    load_data = PythonOperator(
        task_id="load_data",
        python_callable=_load_data
    )

    end = DummyOperator(task_id="end")

    start >> transform_data >> load_data >> end