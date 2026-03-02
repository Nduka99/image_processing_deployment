"""
Test script to verify the FastAPI endpoints and the integrated ML Pipeline.
Uploads a sample test image from data/raw to the /predict endpoint.
"""
import os
import time
import requests

API_URL = "http://127.0.0.1:8000"

def get_sample_image():
    """Find a random image from the raw dataset to test."""
    test_dir = os.path.join("data", "raw", "test_images")
    if not os.path.exists(test_dir):
        print("Test images directory not found. Please ensure data is organized.")
        return None
        
    for file in os.listdir(test_dir):
        if file.endswith((".jpg", ".png")):
            return os.path.join(test_dir, file)
            
    return None

def test_health():
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        print("Health Check PASS.\n")
    except Exception as e:
        print(f"Health Check FAIL: {e}\n")

def test_predict(image_path):
    print(f"Testing /predict endpoint with {image_path}...")
    try:
        start_time = time.time()
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
            response = requests.post(f"{API_URL}/predict", files=files)
            
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            print(f"E2E API Time (Network + Features + Inference): {elapsed:.3f}s\n")
            print("Prediction PASS.\n")
        else:
            print(f"Failed with response: {response.text}\n")
    except Exception as e:
        print(f"Prediction FAIL: {e}\n")

def main():
    img_path = get_sample_image()
    if not img_path:
        return
        
    test_health()
    test_predict(img_path)

if __name__ == "__main__":
    # Test usually requires the server to be running on 8000
    # Make sure to run `uvicorn api.main:app --port 8000` before running this script
    main()
