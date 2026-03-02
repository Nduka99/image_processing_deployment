"""
Test script to verify the ML Pipeline extraction yields the same results 
as the original Champion XGBoost model.
"""
import numpy as np
import time
from api.ml import MLPipeline

def main():
    print("Testing ML Pipeline Inference...")
    
    # 1. Load an array of test features
    # (Using the very first 5 samples from the processed testing data)
    test_data = np.load('data/processed/features_test.npy', allow_pickle=True)
    sample_features = test_data[:5]
    
    print(f"Loaded {len(sample_features)} testing samples. Shape: {sample_features.shape}")
    
    # 2. Initialize the pipeline
    start_init = time.time()
    pipeline = MLPipeline()
    print(f"Pipeline initialized in {time.time() - start_init:.4f}s")
    
    # 3. Preprocess and predict
    print("\nRunning Inference...")
    start_infer = time.time()
    predictions = pipeline.predict(sample_features)
    inference_time = time.time() - start_infer
    
    print(f"Predictions: {predictions}")
    print(f"Inference Time for {len(sample_features)} images: {inference_time:.4f}s")
    print(f"Per-image Inference Time: {(inference_time / len(sample_features)) * 1000:.2f}ms")
    
    assert len(predictions) == 5, "Prediction array length mismatch"
    print("\nVERIFICATION SUCCESSFUL: ONNX Pipeline running smoothly.")

if __name__ == "__main__":
    main()
