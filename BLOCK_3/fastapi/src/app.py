import pandas as pd
import mlflow
from pydantic import BaseModel
from typing import Union
from fastapi import FastAPI, File, UploadFile, HTTPException

description = """
This API provide endpoints for financial fraud detection

* `/predict` To predict whether a payment is fraudulent or not, on one observation
* `/batch-predict` To predict whether a payment is fraudulent or not, on a batch of observation
"""

tags_metadata = [

    {
        "name": "Machine-Learning"
    }
]

app = FastAPI(
    title="Automatic Fraud Detection",
    description=description,
    version="0.1",
    openapi_tags=tags_metadata
)

MODEL_NAME = "mlflow-fraud-detection-XGBC"
MODEL_VERSION = "latest"

class PredictionFeatures(BaseModel):
    category: str
    merchant: str
    amt: Union[int, float]
    gender: str
    last: str
    first: str
    lat: Union[int, float]
    long: Union[int, float]
    city_pop: Union[int, float]
    zip: Union[int, float]
    job: str
    dob: str


@app.post("/predict", tags=["Machine-Learning"])
async def predict(predictionFeatures: PredictionFeatures):
    """
    Prediction for one observation. Endpoint will return a dictionnary like this:

    ```
    {'prediction': PREDICTION_VALUE}
    ```

    You need to give this endpoint all columns values as dictionnary, or form data.
    """
    try:
        # Read data
        df = pd.DataFrame([predictionFeatures.dict()])

        # Load model
        loaded_model= mlflow.sklearn.load_model(f"models:/{MODEL_NAME}/{MODEL_VERSION}")

        prediction = loaded_model.predict(df)

        # Format response
        response = {"prediction": prediction.tolist()[0]}

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/batch-predict", tags=["Machine-Learning"])
async def batch_predict(file: UploadFile = File(...)):
    """
    Make prediction on a batch of observation. This endpoint accepts only **csv files** containing
    all the trained columns WITHOUT the target variable.
    """
    try:
        # Read file
        df = pd.read_csv(file.file, index_col="id")

        # Load model
        loaded_model= mlflow.sklearn.load_model(f"models:/{MODEL_NAME}/{MODEL_VERSION}")
        
        predictions = loaded_model.predict(df)

        return predictions.tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))