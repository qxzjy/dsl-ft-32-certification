# IMPORT
import ast
import json
import logging
import pandas as pd
import requests
from airflow import DAG
from airflow.hooks.postgres_hook import PostgresHook
from airflow.hooks.S3_hook import S3Hook
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from pydantic import ValidationError
from pydantic_model import PredictionFeatures


def _fetch_api(**context):
    # Fetch data from API
    response = requests.get(Variable.get("API_FRAUD"))

    # Create a file name containing the date
    json_filename = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_transaction.json"

    # Temprorary save this file into /tmp folder
    with open(f"/tmp/{json_filename}", "w") as f:
        #f.write(f"'{response.json()}'")
        json.dump(response.json(), f)

    # Connect to our S3 bucket and load the file
    s3_hook = S3Hook(aws_conn_id="aws_default")
    s3_hook.load_file(filename=f"/tmp/{json_filename}", key=f"raw_data/{json_filename}", bucket_name=Variable.get("S3_BUCKET_NAME"))

    # Push the filename to the context to use it later
    context["task_instance"].xcom_push(key="json_filename", value=json_filename)


def _validate_data(**context):
    # Filename from the context
    json_filename = context["task_instance"].xcom_pull(key="json_filename")

    # Load the temporary JSON file
    with open(f"/tmp/{json_filename}", "r") as f:
        raw_json_data = json.load(f)

    # Validate data
    try:
        PredictionFeatures(**ast.literal_eval(raw_json_data))  
    except ValidationError as e:
        logging.error(e.errors())
        
        
def _transform_data(**context):
    # Filename from the context
    json_filename = context["task_instance"].xcom_pull(key="json_filename")

    # Load the temporary JSON file
    with open(f"/tmp/{json_filename}", "r") as f:
        raw_json_data = json.load(f)
    raw_json_data = ast.literal_eval(raw_json_data)

    # Transform data into a dataframe
    data = pd.DataFrame(columns=raw_json_data["columns"], data=raw_json_data["data"])

    # Keeping only relevant data for our model
    columns_to_keep = ["category", "merchant", "amt", "gender", "last", "first", "lat", "long", "city_pop", "zip", "job", "dob"]
    data = data[columns_to_keep]
    data["trans_date_trans_time"] = datetime.now()

    # Keep the same filename between the JSON file and the CSV
    csv_filename = json_filename.split(".")[0] + ".csv"
    
    # Put the transformed file in the temp directory
    data.to_csv(f"/tmp/{csv_filename}", index=False)

    # Connect to our S3 bucket and load the file
    s3_hook = S3Hook(aws_conn_id="aws_default")
    s3_hook.load_file(filename=f"/tmp/{csv_filename}", key=f"raw_data/{csv_filename}", bucket_name=Variable.get("S3_BUCKET_NAME"))

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
with DAG(dag_id="etl_api", start_date=datetime(2025, 8, 28), schedule_interval=None, catchup=False) as dag:
    start = DummyOperator(task_id="start")

    fetch_api = PythonOperator(
        task_id="fetch_api",
        python_callable=_fetch_api
    )
    
    validate_data = PythonOperator(
        task_id="validate_data",
        python_callable=_validate_data
    )

    transform_data = PythonOperator(
        task_id="transform_data",
        python_callable=_transform_data
    )

    load_data = PythonOperator(
        task_id="load_data",
        python_callable=_load_data
    )

    end = DummyOperator(task_id="end")

    start >> fetch_api >> validate_data >> transform_data >> load_data >> end