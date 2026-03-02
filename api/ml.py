"""
ML Pipeline encapsulation for deployment.
Loads the XGBoost ONNX model and the StandardScaler.
"""
import os
import numpy as np
import joblib
import onnxruntime as rt

# Define paths relative to the project root (or container workdir `/app`)
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")
ONNX_PATH = os.path.join(MODEL_DIR, "xgboost_champion.onnx")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")

class MLPipeline:
    def __init__(self):
        """Initialize the pipeline, loading the model and scaler only once."""
        print(f"Loading StandardScaler from {SCALER_PATH}...")
        self.scaler = joblib.load(SCALER_PATH)
        
        print(f"Loading ONNX Model from {ONNX_PATH}...")
        self.session = rt.InferenceSession(
            ONNX_PATH, 
            providers=['CPUExecutionProvider']
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def preprocess(self, image_features: np.ndarray) -> np.ndarray:
        """
        Applies the exact standard scaling used during training.
        image_features must be a 2D array of shape (n_samples, 10221)
        """
        if image_features.ndim == 1:
            image_features = image_features.reshape(1, -1)
            
        # Ensure correct type for ONNX
        scaled = self.scaler.transform(image_features)
        return scaled.astype(np.float32)

    def predict(self, image_features: np.ndarray) -> np.ndarray:
        """
        Runs the full pipeline: Preprocess -> Inference
        Returns the predicted class label(s).
        """
        # 1. Scale
        X_scaled = self.preprocess(image_features)
        
        # 2. Predict using ONNX Runtime
        predictions = self.session.run(
            [self.output_name], 
            {self.input_name: X_scaled}
        )[0]
        
        return predictions

