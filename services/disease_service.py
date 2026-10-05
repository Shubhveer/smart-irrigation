"""
Crop disease inference with onnxruntime (no torch/tensorflow needed on the server).

The model is trained offline with ml/train_disease_model.py on PlantVillage and
exported to models/disease_model.onnx. If the model file is missing, the app
falls back to the colour heuristic in image_screening_service.py.
"""
import json
import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from services.i18n import M

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = BASE / "disease_model.onnx"
LABELS_PATH = BASE / "disease_labels.json"
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
MIN_CONFIDENCE = 0.60

ADVICE = {
    "blight": "Fungal disease: avoid overhead watering, irrigate early morning, improve airflow.",
    "mold": "Fungal disease: reduce humidity and leaf wetness; water at the base only.",
    "mildew": "Fungal disease: avoid wetting leaves; water at the base in the morning.",
    "rust": "Fungal disease: keep foliage dry; do not irrigate in the evening.",
    "scab": "Fungal disease: avoid wetting leaves; remove fallen infected leaves.",
    "rot": "Fungal disease: improve drainage and avoid over-watering.",
    "spot": "Leaf spot: water at the base and avoid splashing soil onto leaves.",
    "mite": "Mites thrive in hot, dry conditions: keep soil moisture steady and inspect leaf undersides.",
    "virus": "Viral disease: no cure. Remove infected plants and control insect vectors.",
    "greening": "Bacterial disease spread by insects: remove infected trees and control psyllids.",
}
CONFIRM_NOTE = "Preliminary AI result. Confirm with an agriculture officer before applying any pesticide."


def is_available() -> bool:
    return MODEL_PATH.exists() and LABELS_PATH.exists()


@lru_cache(maxsize=1)
def _load():
    """Loaded once, on first request, so app start-up stays fast and light."""
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    sess = ort.InferenceSession(str(MODEL_PATH), opts, providers=["CPUExecutionProvider"])
    labels = json.loads(LABELS_PATH.read_text())
    logger.info("Disease model loaded (%d classes)", len(labels))
    return sess, labels


IMG_SIZE = 224


def preprocess(file_obj) -> np.ndarray:
    """Open an image and return a 1x3x224x224 float32 array.

    The training script (ml/train_cpu_transfer.py) imports this exact function, so training and the
    app always see identical pixels. Phone photos are centre-cropped to a square (not squashed).
    """
    img = Image.open(file_obj)
    img.draft("RGB", (2 * IMG_SIZE, 2 * IMG_SIZE))  # fast JPEG downscale while decoding big photos
    img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    arr = (np.asarray(img, dtype=np.float32) / 255.0 - MEAN) / STD
    return arr.transpose(2, 0, 1)[None]


_preprocess = preprocess


def _advice(disease: str) -> str:
    d = disease.lower()
    if "healthy" in d:
        return "Plant looks healthy. Continue normal irrigation."
    return next((v for k, v in ADVICE.items() if k in d), "Consult a local agriculture officer.")


def _looks_like_photo(x: np.ndarray) -> bool:
    """Reject blank/flat images. The model only knows 38 classes and would still answer confidently.
    Thresholds calibrated on PlantVillage: rejects 0.3% of real leaf photos."""
    rgb = (x[0].transpose(1, 2, 0) * STD + MEAN) * 255.0
    mx, mn = rgb.max(2), rgb.min(2)
    saturation = float(((mx - mn) / (mx + 1e-6)).mean())
    return float(rgb.mean(2).std()) >= 12 and saturation >= 0.10


def predict(file_obj, top_k: int = 3) -> dict:
    x = _preprocess(file_obj)
    if not _looks_like_photo(x):
        return {
            "confident": False,
            "top_predictions": [],
            "finding": "No leaf detected in this image",
            "recommendation": ["Upload a clear, well-lit, close photo of a single leaf."],
        }
    sess, labels = _load()
    logits = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]
    e = np.exp(logits - logits.max())
    probs = e / e.sum()
    top = probs.argsort()[::-1][:top_k]
    preds = []
    for i in top:
        plant, _, disease = labels[i].partition("___")
        preds.append({"plant": plant.replace("_", " ").strip(), "disease": disease.replace("_", " ").strip(),
                      "confidence": round(float(probs[i]), 4)})
    best = preds[0]
    confident = best["confidence"] >= MIN_CONFIDENCE
    return {
        "confident": confident,
        "top_predictions": preds,
        "finding": (M("{plant}: {disease} ({pct}% confidence)", plant=best["plant"], disease=best["disease"],
                      pct=round(best["confidence"] * 100))
                    if confident else "Low confidence: could not identify the problem reliably"),
        "recommendation": ([_advice(best["disease"]), CONFIRM_NOTE] if confident else
                           ["Retake a clear, well-lit, close photo of a single leaf and try again."]),
    }
