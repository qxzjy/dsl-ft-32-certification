from typing import Union
from pydantic import BaseModel

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