import pandas as pd
import time
import mlflow
import os
from xgboost import XGBClassifier
from mlflow.models.signature import infer_signature
from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

if __name__ == "__main__":

    # Set your variables for your environment
    # EXPERIMENT_NAME="fraud_detection"
    # experiment = mlflow.set_experiment(EXPERIMENT_NAME)

    # client = mlflow.tracking.MlflowClient()
    # run = client.create_run(experiment.experiment_id)

    print("training model...")
    
    # Time execution
    start_time = time.time()

    # Call mlflow autolog
    mlflow.sklearn.autolog(log_models=False) # We won't log models right away

     # Import dataset
    dataset = pd.read_csv(
        "https://lead-program-assets.s3.eu-west-3.amazonaws.com/M05-Projects/fraudTest.csv",
        index_col=0
    )

    # Drop useless columns
    columns_to_keep = ["category", "merchant", "amt", "gender", "last", "first", "lat", "long", "city_pop", "zip", "job", "dob", "is_fraud"]
    df = dataset[columns_to_keep]

    # X, y split
    target_variable = "is_fraud"
    X = df.drop(target_variable, axis = 1)
    y = df[target_variable]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 3)

    numerical_features = X.select_dtypes(exclude="object").columns
    categorical_features = X.select_dtypes(include="object").columns

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), categorical_features)
        ]
    )
    
    # Pipeline
    model = Pipeline(
        steps=[
            ("Preprocessing", preprocessor),
            (
                "Classifier",
                XGBClassifier(learning_rate=0.1, max_depth=3)
            ),
        ],
        verbose=True
    )

    # Log experiment to MLFlow
    with mlflow.start_run() as run:
        model.fit(X_train, y_train)
        predictions = model.predict(X_train)

        try :
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="mlflow-fraud-detection",
                registered_model_name="mlflow-fraud-detection-XGBC",
                signature=infer_signature(X_train, predictions),
            )
        except mlflow.exceptions.MlflowException as e:
            print("⚠️ Model logging failed:", e)
        
    print("...Done!")
    print(f"---Total training time: {time.time()-start_time}")

    