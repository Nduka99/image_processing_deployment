import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
import os

print("Loading training features...")
features_path = os.path.join("data", "processed", "features_all.npy")
if not os.path.exists(features_path):
    print(f"Error: Could not find {features_path}")
    exit(1)

X_all = np.load(features_path, allow_pickle=True)
print(f"Loaded feature shape: {X_all.shape}")

print("Fitting StandardScaler...")
scaler = StandardScaler()
scaler.fit(X_all)

out_path = os.path.join("model", "scaler.joblib")
print(f"Saving StandardScaler to {out_path}...")
joblib.dump(scaler, out_path)
print("Done!")
