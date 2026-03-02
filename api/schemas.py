from pydantic import BaseModel

class PredictionResponse(BaseModel):
    success: bool
    prediction: str
    confidence: float
    prob_cat: float = 0.0
    prob_dog: float = 0.0
    message: str
