# IMPORT
import os
import pandas as pd
import requests
from airflow import DAG
from airflow.hooks.postgres_hook import PostgresHook
from airflow.hooks.S3_hook import S3Hook
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from datetime import datetime
from sqlalchemy import update, MetaData, Table
from sqlalchemy.orm import Session


def _fetch_db(**context):
    # Connect to PostgreSQL and get data
    postgres_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = postgres_hook.get_sqlalchemy_engine()
    data = pd.read_sql("SELECT * FROM {} WHERE price IS NULL".format(Variable.get("TABLE_HOUSING_PRICES")), engine, index_col="id")

    if len(data) != 0:
        # Separate target variables from features
        data.drop("price", axis=1, inplace=True)

        # Create a file name containing the date
        csv_filename = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_predictions.csv"

        # Put the predictions file in the temp directory
        data.to_csv(f"/tmp/{csv_filename}")

        # Push the filename to the context to use it later
        context["task_instance"].xcom_push(key="csv_filename", value=csv_filename)
        return "predict"
    else :
        return "end"


def _predict(**context):
    # Filename from the context
    csv_filename = context["task_instance"].xcom_pull(key="csv_filename")

    # Get batch predictions from FastAPI
    with open(f"/tmp/{csv_filename}", "rb") as f:
        file = {"file": (os.path.basename(f"/tmp/{csv_filename}"), f, "text/csv")}
        response = requests.post(Variable.get("API_ML"), files=file)

    predictions = response.json()
    
    # Load data from CSV and add predictions
    data = pd.read_csv(f"/tmp/{csv_filename}")
    data["price"] = predictions

    # Put the data with predictions in the temp directory
    data.to_csv(f"/tmp/{csv_filename}")

    # Connect to our S3 bucket and load the file
    s3_hook = S3Hook(aws_conn_id="aws_default")
    s3_hook.load_file(filename=f"/tmp/{csv_filename}", key=f"raw_data/{csv_filename}", bucket_name=Variable.get("S3_BUCKET_NAME"))


def _load_data(**context):
    # Filename from the context
    csv_filename = context["task_instance"].xcom_pull(key="csv_filename")

    # Load data from CSV
    data = pd.read_csv(f"/tmp/{csv_filename}", index_col="id")
    
    # Connect to PostgreSQL and load data
    postgres_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = postgres_hook.get_sqlalchemy_engine()
    
    metadata = MetaData()
    housing_prices_table = Table(Variable.get("TABLE_HOUSING_PRICES"), metadata, autoload_with=engine)

    with Session(engine) as session:
        for index, row in data.iterrows():
            stmt = (update(housing_prices_table).where(housing_prices_table.c.id==index).values(price=row["price"]))
            session.execute(stmt)

        session.commit()


with DAG(dag_id="price_prediction", start_date=datetime(2025, 8, 28), schedule_interval=None, catchup=False) as dag:
    start = DummyOperator(task_id="start")

    fetch_db = BranchPythonOperator(
        task_id='fetch_db',
        python_callable=_fetch_db,
        provide_context=True
    )

    predict = PythonOperator(
        task_id="predict",
        python_callable=_predict
    )

    load_data = PythonOperator(
        task_id="load_data",
        python_callable=_load_data
    )

    end = DummyOperator(task_id="end", trigger_rule="none_failed")

    start >> fetch_db >> [predict, end]
    predict >> load_data >> end