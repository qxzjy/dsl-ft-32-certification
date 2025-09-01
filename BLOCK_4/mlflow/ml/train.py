import pandas as pd
import time
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

if __name__ == "__main__":

    print("Training model...")
    
    # Time execution
    start_time = time.time()

    # Call mlflow autolog
    mlflow.sklearn.autolog(log_models=False) # We won't log models right away

     # Import dataset
    dataset = pd.read_csv("data/real_estate_dataset.csv", index_col=0)

    # X, y split
    target_variable = "Price"
    X = dataset.drop([target_variable] , axis = 1)
    X = X.set_axis(["square_feet", "num_bedrooms", "num_bathrooms", "num_floors", "year_built", "has_garden", "has_pool", "garage_size", "location_score", "distance_to_center"], axis=1)
    y = dataset[target_variable]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 3)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), X.columns)]
    )
    # Pipeline
    model = Pipeline(steps=[
        ("Preprocessing", preprocessor),
        ("Regressor",LinearRegression())
    ], verbose=True)

    # Log experiment to MLFlow
    with mlflow.start_run() as run:
        model.fit(X_train, y_train)
        predictions = model.predict(X_train)

        try :
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="housing-prices-estimator",
                registered_model_name="housing-prices-estimator-LR",
                signature=infer_signature(X_train, predictions),
            )
        except mlflow.exceptions.MlflowException as e:
            print("⚠️ Model logging failed:", e)
        
    print("...Done!")
    print(f"---Total training time: {time.time()-start_time}")

    