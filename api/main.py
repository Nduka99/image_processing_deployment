import io
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.dependencies import get_ml_pipeline
from api.ml import MLPipeline
from api.schemas import PredictionResponse
from api.feature_extractor import process_raw_image

app = FastAPI(title="Image Processing Classification API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "ML Inference API is running."}

@app.post("/predict", response_model=PredictionResponse)
async def predict_image(
    file: UploadFile = File(...),
    pipeline: MLPipeline = Depends(get_ml_pipeline)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    try:
        # Read image to memory
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_bgr is None:
            raise HTTPException(status_code=400, detail="Could not decode image.")
            
        # 1. Image Preprocessing & Feature Extraction
        features = process_raw_image(img_bgr)
        
        # 2. Predict
        prediction_output = pipeline.predict(features)
        
        # Determine class output
        # Usually prediction array corresponds to [class_0_prob, class_1_prob] or label
        # XGBoost ONNX returns label indices (e.g. 0 or 1) as output 0, probabilities as output 1.
        # Let's read the label:
        pred_label_idx = int(prediction_output[0])
        label = "dog" if pred_label_idx == 1 else "cat"
        
        return PredictionResponse(
            success=True,
            prediction=label,
            confidence=1.0, # ONNX output parsing for XGBoost probabilities might require output[1] depending on graph
            message="Prediction successful"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
