"""
06_evaluate_all.py
------------------
Loads all three trained models, evaluates them on the test set,
and produces a side-by-side comparison:
  - Accuracy, precision, recall, F1 (macro & weighted)
  - Per-class F1 comparison bar chart
  - Side-by-side confusion matrices
  - Combined summary table saved as models/comparison_report.csv
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report
)

# ── Configuration ────────────────────────────────────────────────────────────
SPLIT_DIR   = Path("data/split")
CLASS_FILE  = Path("data/class_names.txt")
YOLO_DIR    = Path("data/yolo")
OUT_DIR     = Path("models")

MOBILENET_PATH   = Path("models/mobilenetv2/best_model.keras")
EFFICIENTNET_PATH = Path("models/efficientnet/best_model.keras")
YOLO_PATH        = Path("models/yolov8/best.pt")

IMG_SIZE    = (224, 224)
BATCH_SIZE  = 32
# ─────────────────────────────────────────────────────────────────────────────


def load_class_names() -> list[str]:
    with open(CLASS_FILE) as f:
        return [line.strip().split("\t")[1] for line in f if line.strip()]


# ── Keras models ──────────────────────────────────────────────────────────────

def predict_keras(model_path: Path, class_names: list[str], rescale=True):
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    print(f"\n[INFO] Loading Keras model: {model_path}")
    model = tf.keras.models.load_model(model_path)

    scale = 1.0 / 255 if rescale else 1.0
    gen = ImageDataGenerator(rescale=scale).flow_from_directory(
        SPLIT_DIR / "test",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )
    y_prob = model.predict(gen, verbose=1)
    y_pred = np.argmax(y_prob, axis=1)
    y_true = gen.classes[:len(y_pred)]
    return y_true, y_pred


def predict_yolov8(class_names: list[str]):
    from ultralytics import YOLO

    print(f"\n[INFO] Loading YOLOv8 model: {YOLO_PATH}")
    model = YOLO(YOLO_PATH)

    results = model.val(
        data=str(YOLO_DIR.resolve()),
        split="test",
        imgsz=IMG_SIZE[0],
        batch=BATCH_SIZE,
        verbose=False,
    )
    # Ultralytics stores confusion matrix in results
    try:
        cm = results.confusion_matrix.matrix.astype(int)
        y_true, y_pred = [], []
        for true_idx in range(len(cm)):
            for pred_idx in range(len(cm)):
                count = cm[true_idx][pred_idx]
                y_true.extend([true_idx] * count)
                y_pred.extend([pred_idx] * count)
        return np.array(y_true), np.array(y_pred)
    except Exception as e:
        print(f"[WARNING] Could not extract per-image predictions from YOLO: {e}")
        # Fall back to scalar metrics
        top1 = float(results.top1) if hasattr(results, "top1") else float("nan")
        return None, None, top1


# ── Metrics ──────────────────────────────────────────────────────────────────

def compute_metrics(y_true, y_pred, class_names) -> dict:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_weighted": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "per_class_f1": f1_score(y_true, y_pred, average=None, zero_division=0),
    }


# ── Plots ────────────────────────────────────────────────────────────────────

def plot_comparison_bar(all_metrics: dict, class_names: list[str]):
    model_names = list(all_metrics.keys())
    metrics_to_plot = ["accuracy", "f1_macro", "f1_weighted", "precision_macro", "recall_macro"]
    labels = ["Accuracy", "F1 Macro", "F1 Weighted", "Precision Macro", "Recall Macro"]

    x = np.arange(len(metrics_to_plot))
    width = 0.25
    colors = ["#4C8BB5", "#E07B54", "#6BAE75"]

    fig, ax = plt.subplots(figsize=(12, 5))
    for i, (model_name, color) in enumerate(zip(model_names, colors)):
        vals = [all_metrics[model_name].get(m, 0) for m in metrics_to_plot]
        bars = ax.bar(x + i * width, vals, width, label=model_name, color=color, alpha=0.85)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x + width)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison — Test Set Metrics")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "model_comparison_bar.png", dpi=150)
    plt.close()
    print(f"[INFO] Bar chart saved -> {OUT_DIR}/model_comparison_bar.png")


def plot_per_class_f1(all_metrics: dict, class_names: list[str]):
    model_names = list(all_metrics.keys())
    n_classes = len(class_names)

    fig, ax = plt.subplots(figsize=(max(14, n_classes * 0.6), 6))
    x = np.arange(n_classes)
    width = 0.28
    colors = ["#4C8BB5", "#E07B54", "#6BAE75"]

    for i, (name, color) in enumerate(zip(model_names, colors)):
        f1s = all_metrics[name].get("per_class_f1", np.zeros(n_classes))
        if len(f1s) < n_classes:
            f1s = np.pad(f1s, (0, n_classes - len(f1s)))
        ax.bar(x + i * width, f1s, width, label=name, color=color, alpha=0.85)

    ax.set_xticks(x + width)
    ax.set_xticklabels(class_names, rotation=45, ha="right", fontsize=7)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("F1 Score")
    ax.set_title("Per-Class F1 Score Comparison")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "per_class_f1.png", dpi=150)
    plt.close()
    print(f"[INFO] Per-class F1 chart saved -> {OUT_DIR}/per_class_f1.png")


def plot_confusion_matrices(all_preds: dict, class_names: list[str]):
    n_models = len(all_preds)
    if n_models == 0:
        return

    fig, axes = plt.subplots(1, n_models, figsize=(9 * n_models, 8))
    if n_models == 1:
        axes = [axes]

    cmaps = ["Blues", "Oranges", "Greens"]
    for ax, (model_name, (y_true, y_pred)), cmap in zip(axes, all_preds.items(), cmaps):
        if y_true is None:
            ax.set_visible(False)
            continue
        cm = confusion_matrix(y_true, y_pred)
        # Normalise for readability
        cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True).clip(min=1)
        sns.heatmap(
            cm_norm,
            annot=len(class_names) <= 15,
            fmt=".2f",
            cmap=cmap,
            xticklabels=class_names,
            yticklabels=class_names,
            ax=ax,
            cbar=False,
        )
        acc = accuracy_score(y_true, y_pred)
        ax.set_title(f"{model_name}\n(Acc={acc:.3f})", fontsize=11)
        ax.set_xlabel("Predicted", fontsize=9)
        ax.set_ylabel("True", fontsize=9)
        ax.tick_params(labelsize=6, rotation=45)

    plt.suptitle("Confusion Matrices (normalised) — Test Set", fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "confusion_matrices.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Confusion matrices saved -> {OUT_DIR}/confusion_matrices.png")


def save_comparison_csv(all_metrics: dict):
    rows = []
    for model_name, m in all_metrics.items():
        rows.append({
            "model": model_name,
            "accuracy": round(m.get("accuracy", float("nan")), 4),
            "f1_macro": round(m.get("f1_macro", float("nan")), 4),
            "f1_weighted": round(m.get("f1_weighted", float("nan")), 4),
            "precision_macro": round(m.get("precision_macro", float("nan")), 4),
            "recall_macro": round(m.get("recall_macro", float("nan")), 4),
        })
    df = pd.DataFrame(rows).set_index("model")
    df.to_csv(OUT_DIR / "comparison_report.csv")
    print(f"\n[INFO] Comparison CSV saved -> {OUT_DIR}/comparison_report.csv")

    print("\n" + "=" * 70)
    print("  FINAL MODEL COMPARISON")
    print("=" * 70)
    print(df.to_string())
    print("=" * 70)

    best = df["accuracy"].idxmax()
    print(f"\n  Best model by accuracy: {best} ({df.loc[best,'accuracy']:.4f})")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Crop Disease Pipeline - Step 6: Evaluate All Models")
    print("=" * 60)

    class_names = load_class_names()
    all_metrics = {}
    all_preds = {}

    # MobileNetV2
    if MOBILENET_PATH.exists():
        y_true, y_pred = predict_keras(MOBILENET_PATH, class_names, rescale=True)
        m = compute_metrics(y_true, y_pred, class_names)
        all_metrics["MobileNetV2"] = m
        all_preds["MobileNetV2"] = (y_true, y_pred)
        print(f"  MobileNetV2  accuracy: {m['accuracy']:.4f}  F1-macro: {m['f1_macro']:.4f}")
    else:
        print(f"[SKIP] MobileNetV2 model not found at {MOBILENET_PATH}")

    # EfficientNetB0
    if EFFICIENTNET_PATH.exists():
        y_true, y_pred = predict_keras(EFFICIENTNET_PATH, class_names, rescale=False)
        m = compute_metrics(y_true, y_pred, class_names)
        all_metrics["EfficientNetB0"] = m
        all_preds["EfficientNetB0"] = (y_true, y_pred)
        print(f"  EfficientNetB0 accuracy: {m['accuracy']:.4f}  F1-macro: {m['f1_macro']:.4f}")
    else:
        print(f"[SKIP] EfficientNetB0 model not found at {EFFICIENTNET_PATH}")

    # YOLOv8
    if YOLO_PATH.exists():
        result = predict_yolov8(class_names)
        if len(result) == 3:
            y_true, y_pred, fallback_acc = result
        else:
            y_true, y_pred = result
            fallback_acc = None

        if y_true is not None and y_pred is not None:
            m = compute_metrics(y_true, y_pred, class_names)
            all_metrics["YOLOv8s-cls"] = m
            all_preds["YOLOv8s-cls"] = (y_true, y_pred)
            print(f"  YOLOv8s-cls accuracy: {m['accuracy']:.4f}  F1-macro: {m['f1_macro']:.4f}")
        elif fallback_acc is not None:
            all_metrics["YOLOv8s-cls"] = {"accuracy": fallback_acc}
            print(f"  YOLOv8s-cls accuracy: {fallback_acc:.4f} (from scalar val result)")
    else:
        print(f"[SKIP] YOLOv8 model not found at {YOLO_PATH}")

    if not all_metrics:
        print("\n[ERROR] No trained models found. Train at least one model first.")
        return

    # Plots
    plot_comparison_bar(all_metrics, class_names)
    if len({k: v for k, v in all_metrics.items() if "per_class_f1" in v}) > 0:
        plot_per_class_f1(all_metrics, class_names)
    if all_preds:
        plot_confusion_matrices(all_preds, class_names)

    save_comparison_csv(all_metrics)
    print("\n[DONE] Evaluation complete.")


if __name__ == "__main__":
    main()
