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
from mail_utility import SimpleMailSender
from sqlalchemy import update, MetaData, Table
from sqlalchemy.orm import Session


def _fetch_db(**context):
    # Connect to PostgreSQL and get data
    postgres_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = postgres_hook.get_sqlalchemy_engine()
    data = pd.read_sql(f"SELECT * FROM {Variable.get("TABLE_FRAUD")} WHERE is_fraud IS NULLf", engine, index_col="id")

    if len(data) != 0:
        # Separate target variables from features
        data.drop("is_fraud", axis=1, inplace=True)

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
    with open(f"/tmp/{csv_filename}", 'rb') as f:
        file = {'file': (os.path.basename(f"/tmp/{csv_filename}"), f, 'text/csv')}
        response = requests.post(Variable.get("API_ML"), files=file)
    predictions = response.json()

    # Load data from CSV and add predictions
    data = pd.read_csv(f"/tmp/{csv_filename}")
    data['is_fraud'] = predictions

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
    fraud_detection_table = Table(Variable.get("TABLE_FRAUD"), metadata, autoload_with=engine)

    with Session(engine) as session:
        for index, row in data.iterrows():
            stmt = (update(fraud_detection_table).where(fraud_detection_table.c.id==index).values(is_fraud=row["is_fraud"]))
            session.execute(stmt)

        session.commit()


def _send_notification(**context):
    # Filename from the context
    csv_filename = context["task_instance"].xcom_pull(key="csv_filename")

    # Load data from CSV
    data = pd.read_csv(f"/tmp/{csv_filename}", index_col="id")
    data = data[data["is_fraud"]==1]
    
    if len(data) != 0:
        fraud_list_string = ""

        for index, row in data.iterrows():
            fraud_list_string += "#{} ({}$)\n".format(index, row["amt"])

        body = f"Liste des transactions concernées ({len(data)}) :\n{fraud_list_string}\n\n Pour plus de détails, consulter le dashboard : https://qxzjy-streamlit-fraud-detection.hf.space"  

        SimpleMailSender.send_email(Variable.get("SENDER_EMAIL"), Variable.get("RECEIVER_EMAIL"), "Détection de transactions frauduleuses !", body)


with DAG(dag_id="fraud_detection", start_date=datetime(2025, 8, 28), schedule_interval=None, catchup=False) as dag:
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

    send_notification = PythonOperator(
        task_id="send_notification",
        python_callable=_send_notification
    )

    end = DummyOperator(task_id="end", trigger_rule="all_done")

    start >> fetch_db >> [predict, end]
    predict >> [load_data, send_notification] >> end