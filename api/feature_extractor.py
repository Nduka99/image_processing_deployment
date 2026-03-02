import cv2
import numpy as np
import mahotas
from skimage.feature import hog, local_binary_pattern
from skimage.filters import gabor
from scipy.stats import skew

IMG_SIZE = 128

def smart_resize(img, target_size=IMG_SIZE):
    h, w = img.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(img, (new_w, new_h), interpolation=interp)

    pad_top = (target_size - new_h) // 2
    pad_bot = target_size - new_h - pad_top
    pad_left = (target_size - new_w) // 2
    pad_right = target_size - new_w - pad_left

    return cv2.copyMakeBorder(resized, pad_top, pad_bot, pad_left, pad_right, borderType=cv2.BORDER_REPLICATE)

def apply_clahe(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

def apply_bilateral(img):
    return cv2.bilateralFilter(img, d=7, sigmaColor=50, sigmaSpace=50)

def preprocess_image(img):
    img = smart_resize(img, IMG_SIZE)
    img = apply_clahe(img)
    img = apply_bilateral(img)
    return img

def extract_hog_features(gray):
    hog_fine = hog(gray, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2), block_norm='L2-Hys', feature_vector=True)
    hog_coarse = hog(gray, orientations=9, pixels_per_cell=(16, 16), cells_per_block=(2, 2), block_norm='L2-Hys', feature_vector=True)
    return np.concatenate([hog_fine, hog_coarse])

def extract_lbp_features(gray):
    features = []
    for radius, n_points in [(1, 8), (2, 16), (3, 24)]:
        lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
        hist, _ = np.histogram(lbp, bins=n_points + 2, range=(0, n_points + 2), density=True)
        features.append(hist)
    return np.concatenate(features)

def extract_color_histogram_features(img_rgb):
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    features = []
    for i, (lo, hi) in enumerate([(0, 180), (0, 256), (0, 256)]):
        hist = cv2.calcHist([hsv], [i], None, [32], [lo, hi])
        features.append(hist.flatten() / hist.sum())
    for i in range(3):
        hist = cv2.calcHist([lab], [i], None, [32], [0, 256])
        features.append(hist.flatten() / hist.sum())
    return np.concatenate(features)

def extract_color_moments(img_rgb):
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV).astype(np.float64)
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
    rgb = img_rgb.astype(np.float64)
    features = []
    for color_img in [rgb, hsv, lab]:
        for c in range(3):
            ch = color_img[:, :, c].flatten()
            features.extend([np.mean(ch), np.std(ch), skew(ch)])
    return np.array(features)

def extract_haralick_features(gray):
    gray_uint8 = (gray * 255).astype(np.uint8) if gray.max() <= 1.0 else gray.astype(np.uint8)
    try:
        return mahotas.features.haralick(gray_uint8, return_mean=True)
    except Exception:
        return np.zeros(13)

def extract_hu_moments(gray):
    moments = cv2.moments(gray)
    hu = cv2.HuMoments(moments).flatten()
    return -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)

def extract_edge_features(gray):
    gray_uint8 = (gray * 255).astype(np.uint8) if gray.max() <= 1.0 else gray.astype(np.uint8)
    edges = cv2.Canny(gray_uint8, 50, 150)
    edge_density = np.mean(edges > 0)
    gx = cv2.Sobel(gray_uint8, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_uint8, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(gx**2 + gy**2)
    orientation = np.arctan2(gy, gx)
    orient_hist, _ = np.histogram(orientation[magnitude > np.mean(magnitude)], bins=8, range=(-np.pi, np.pi), density=True)
    h, w = edges.shape
    quad_densities = [
        np.mean(edges[:h//2, :] > 0), np.mean(edges[h//2:, :] > 0),
        np.mean(edges[:, :w//2] > 0), np.mean(edges[:, w//2:] > 0),
    ]
    grad_stats = [np.mean(magnitude), np.std(magnitude), np.max(magnitude)]
    return np.concatenate([[edge_density], orient_hist, quad_densities, grad_stats])

def extract_gabor_features(gray):
    gray_float = gray.astype(np.float64) / 255.0 if gray.max() > 1.0 else gray.astype(np.float64)
    features = []
    for freq in [0.1, 0.2, 0.3, 0.4]:
        for theta in [0, np.pi/6, np.pi/3, np.pi/2, 2*np.pi/3, 5*np.pi/6]:
            filt_real, _ = gabor(gray_float, frequency=freq, theta=theta)
            features.extend([np.mean(filt_real), np.std(filt_real)])
    return np.array(features)

def process_raw_image(img_bgr):
    """Expects raw BGR image (from cv2.imdecode). Returns (1, 10221) feature array."""
    img_bgr = preprocess_image(img_bgr)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    features = np.concatenate([
        extract_hog_features(gray),
        extract_lbp_features(gray),
        extract_color_histogram_features(img_rgb),
        extract_color_moments(img_rgb),
        extract_haralick_features(gray),
        extract_hu_moments(gray),
        extract_edge_features(gray),
        extract_gabor_features(gray),
    ])
    
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
    return features.reshape(1, -1)
