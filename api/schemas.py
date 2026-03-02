from pydantic import BaseModel

class PredictionResponse(BaseModel):
    success: bool
    prediction: str
    confidence: float
    message: str
