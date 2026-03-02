import io
import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Serve the frontend UI
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(FRONTEND_DIR):
    @app.get("/")
    def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    # Also mount at root level so index.css, app.js resolve correctly
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

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
            
        # 1. Image Preprocessing & Feature Extraction (raw 10,221 features)
        raw_features = process_raw_image(img_bgr)
        
        # 2. CRITICAL: Apply the StandardScaler that was fitted during training.
        #    Without this, the ONNX model receives unscaled features and predictions are garbage.
        scaled_features = pipeline.preprocess(raw_features)
        
        # 3. Run ONNX inference with ALL outputs (label + probabilities)
        outputs = pipeline.session.run(None, {pipeline.input_name: scaled_features})
        
        pred_label_idx = int(outputs[0][0])
        
        # 4. Extract probabilities from outputs[1]
        #    XGBoost ONNX returns: outputs[0] = labels, outputs[1] = probabilities array shape (1, 2)
        confidence = 1.0
        prob_cat = 0.0
        prob_dog = 0.0
        
        if len(outputs) > 1:
            try:
                prob_array = outputs[1][0]
                prob_cat = float(prob_array[0])
                prob_dog = float(prob_array[1])
                confidence = max(prob_cat, prob_dog)
            except Exception:
                pass
                
        # 5. OOD check: if neither class exceeds 51%, classify as unknown
        if confidence < 0.51:
            return PredictionResponse(
                success=True,
                prediction="unknown",
                confidence=confidence,
                prob_cat=prob_cat,
                prob_dog=prob_dog,
                message="Hmm... that doesn't look like a cat or a dog! Are you trying to trick me?"
            )

        label = "dog" if pred_label_idx == 1 else "cat"
        
        return PredictionResponse(
            success=True,
            prediction=label,
            confidence=confidence, 
            prob_cat=prob_cat,
            prob_dog=prob_dog,
            message="Prediction successful"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
