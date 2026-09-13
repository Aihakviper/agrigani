"""
07_predict.py
-------------
Run crop disease prediction on a single image using any of the trained models.

Usage:
  python 07_predict.py --image path/to/leaf.jpg
  python 07_predict.py --image leaf.jpg --model mobilenet
  python 07_predict.py --image leaf.jpg --model efficientnet
  python 07_predict.py --image leaf.jpg --model yolov8
  python 07_predict.py --image leaf.jpg --model best   (auto-selects highest accuracy)

Output:
  - Predicted disease label
  - Confidence score
  - Top-5 predictions
  - Optional: saves annotated image to predictions/
"""

import argparse
import sys
from pathlib import Path

import numpy as np

CLASS_FILE   = Path("data/class_names.txt")
MOBILENET_PATH    = Path("models/mobilenetv2/best_model.keras")
EFFICIENTNET_PATH = Path("models/efficientnet/best_model.keras")
YOLO_PATH         = Path("models/yolov8/best.pt")
COMPARISON_CSV    = Path("models/comparison_report.csv")
PRED_DIR          = Path("predictions")

IMG_SIZE = (224, 224)


def load_class_names() -> list[str]:
    with open(CLASS_FILE) as f:
        return [line.strip().split("\t")[1] for line in f if line.strip()]


def select_best_model() -> str:
    """Read comparison CSV and return model key with highest accuracy."""
    if not COMPARISON_CSV.exists():
        print("[INFO] No comparison report found — defaulting to EfficientNetB0")
        return "efficientnet"

    import pandas as pd
    df = pd.read_csv(COMPARISON_CSV, index_col="model")
    best = df["accuracy"].idxmax()
    name_map = {
        "MobileNetV2": "mobilenet",
        "EfficientNetB0": "efficientnet",
        "YOLOv8s-cls": "yolov8",
    }
    key = name_map.get(best, "efficientnet")
    print(f"[INFO] Best model from comparison: {best} (key={key})")
    return key


# ── Keras predictor ───────────────────────────────────────────────────────────

def predict_keras(image_path: Path, model_path: Path, class_names: list[str], rescale=True):
    import tensorflow as tf
    from PIL import Image

    print(f"[INFO] Loading Keras model: {model_path.name}")
    model = tf.keras.models.load_model(model_path)

    img = Image.open(image_path).convert("RGB").resize(IMG_SIZE, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32)
    if rescale:
        arr /= 255.0
    arr = np.expand_dims(arr, axis=0)

    probs = model.predict(arr, verbose=0)[0]
    return probs, class_names


# ── YOLO predictor ────────────────────────────────────────────────────────────

def predict_yolo(image_path: Path, class_names: list[str]):
    from ultralytics import YOLO

    print(f"[INFO] Loading YOLOv8 model: {YOLO_PATH.name}")
    model = YOLO(YOLO_PATH)

    results = model.predict(str(image_path), imgsz=IMG_SIZE[0], verbose=False)
    r = results[0]
    probs = r.probs.data.cpu().numpy()
    return probs, class_names


# ── Pretty output ─────────────────────────────────────────────────────────────

def format_prediction(probs: np.ndarray, class_names: list[str], top_k=5):
    top_idx = np.argsort(probs)[::-1][:top_k]

    print("\n" + "=" * 55)
    print("  CROP DISEASE PREDICTION")
    print("=" * 55)
    print(f"  {'Rank':<5} {'Disease / Condition':<38} {'Confidence':>10}")
    print("-" * 55)
    for rank, idx in enumerate(top_idx, 1):
        marker = " <-- PREDICTION" if rank == 1 else ""
        print(f"  {rank:<5} {class_names[idx]:<38} {probs[idx]*100:>9.2f}%{marker}")
    print("=" * 55)

    top_class = class_names[top_idx[0]]
    confidence = probs[top_idx[0]]

    # Disease vs healthy interpretation
    is_healthy = "healthy" in top_class.lower()
    severity = (
        "HEALTHY" if is_healthy
        else "HIGH CONFIDENCE — Seek treatment" if confidence > 0.85
        else "MODERATE CONFIDENCE — Consider further inspection" if confidence > 0.60
        else "LOW CONFIDENCE — Manual inspection recommended"
    )
    print(f"\n  Status: {severity}")
    print()

    return top_class, confidence


def save_annotated(image_path: Path, top_class: str, confidence: float):
    from PIL import Image, ImageDraw, ImageFont

    PRED_DIR.mkdir(exist_ok=True)
    img = Image.open(image_path).convert("RGB")
    img = img.resize((400, 400), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    # Background bar
    bar_color = (50, 180, 80) if "healthy" in top_class.lower() else (200, 60, 50)
    draw.rectangle([(0, 360), (400, 400)], fill=(*bar_color, 200))

    label = f"{top_class}  {confidence*100:.1f}%"
    try:
        from PIL import ImageFont
        font = ImageFont.load_default(size=14)
    except Exception:
        font = None

    draw.text((10, 370), label, fill="white", font=font)

    out_path = PRED_DIR / f"pred_{image_path.stem}.jpg"
    img.save(out_path, "JPEG", quality=95)
    print(f"[INFO] Annotated image saved -> {out_path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Crop Disease Predictor")
    parser.add_argument("--image", required=True, help="Path to crop/leaf image")
    parser.add_argument(
        "--model", default="best",
        choices=["mobilenet", "efficientnet", "yolov8", "best"],
        help="Which model to use (default: best from comparison report)"
    )
    parser.add_argument("--top_k", type=int, default=5, help="Show top K predictions")
    parser.add_argument("--save", action="store_true", help="Save annotated prediction image")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"[ERROR] Image not found: {image_path}")
        sys.exit(1)

    if not CLASS_FILE.exists():
        print(f"[ERROR] Class names not found at {CLASS_FILE}")
        print("  Run 02_prepare_dataset.py first.")
        sys.exit(1)

    class_names = load_class_names()
    model_key = args.model if args.model != "best" else select_best_model()

    if model_key == "mobilenet":
        if not MOBILENET_PATH.exists():
            print(f"[ERROR] MobileNetV2 model not found: {MOBILENET_PATH}")
            sys.exit(1)
        probs, names = predict_keras(image_path, MOBILENET_PATH, class_names, rescale=True)

    elif model_key == "efficientnet":
        if not EFFICIENTNET_PATH.exists():
            print(f"[ERROR] EfficientNetB0 model not found: {EFFICIENTNET_PATH}")
            sys.exit(1)
        probs, names = predict_keras(image_path, EFFICIENTNET_PATH, class_names, rescale=False)

    elif model_key == "yolov8":
        if not YOLO_PATH.exists():
            print(f"[ERROR] YOLOv8 model not found: {YOLO_PATH}")
            sys.exit(1)
        probs, names = predict_yolo(image_path, class_names)

    else:
        print(f"[ERROR] Unknown model key: {model_key}")
        sys.exit(1)

    top_class, confidence = format_prediction(probs, names, top_k=args.top_k)

    if args.save:
        save_annotated(image_path, top_class, confidence)


if __name__ == "__main__":
    main()
