"""
05_train_yolov8.py
------------------
Trains YOLOv8 in classification mode (yolo classify) on the crop disease dataset.

Ultralytics YOLOv8 supports image classification natively with:
  yolo classify train data=<path> model=yolov8n-cls.pt epochs=50 imgsz=224

This script wraps the Ultralytics Python API for full control and logging.

Saves:
  models/yolov8/  (ultralytics creates its own run directory here)
  models/yolov8/results.txt  (test accuracy for comparison)
"""

import os
import shutil
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Configuration ────────────────────────────────────────────────────────────
YOLO_DIR     = Path("data/yolo")
MODEL_DIR    = Path("models/yolov8")
CLASS_FILE   = Path("data/class_names.txt")

YOLO_MODEL   = "yolov8s-cls.pt"   # yolov8n-cls (nano) or yolov8s-cls (small)
                                    # change to yolov8m-cls for better accuracy
IMG_SIZE     = 224
BATCH_SIZE   = 32
EPOCHS       = 50
LR0          = 0.001               # initial learning rate
LRF          = 0.01                # final LR = LR0 * LRF
OPTIMIZER    = "Adam"
PATIENCE     = 10                  # early stopping patience
WORKERS      = 4
# ─────────────────────────────────────────────────────────────────────────────


def load_class_names() -> list[str]:
    with open(CLASS_FILE) as f:
        return [line.strip().split("\t")[1] for line in f if line.strip()]


def train_yolov8():
    from ultralytics import YOLO

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Loading base model: {YOLO_MODEL}")
    model = YOLO(YOLO_MODEL)

    print(f"[INFO] Dataset: {YOLO_DIR.resolve()}")
    print(f"[INFO] Training for up to {EPOCHS} epochs (early stop patience={PATIENCE})")

    results = model.train(
        data=str(YOLO_DIR.resolve()),
        task="classify",
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        lr0=LR0,
        lrf=LRF,
        optimizer=OPTIMIZER,
        patience=PATIENCE,
        workers=WORKERS,
        project=str(MODEL_DIR),
        name="train",
        exist_ok=True,
        verbose=True,
        plots=True,          # saves confusion matrix and other plots
        save=True,
        save_period=5,       # save checkpoint every 5 epochs
        augment=True,        # built-in Mosaic / MixUp augmentation
        degrees=15.0,
        flipud=0.0,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
    )

    return model, results


def evaluate_yolov8(model, class_names: list[str]):
    """Run validation on test split and parse metrics."""
    from ultralytics import YOLO

    print("\n[INFO] Evaluating on test set ...")
    test_results = model.val(
        data=str(YOLO_DIR.resolve()),
        split="test",
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        verbose=False,
    )

    # YOLOv8 val returns a Results object — extract top-1 accuracy
    try:
        top1 = float(test_results.top1)
        top5 = float(test_results.top5)
    except Exception:
        top1 = top5 = float("nan")

    print(f"  Test Top-1 Accuracy: {top1:.4f}")
    print(f"  Test Top-5 Accuracy: {top5:.4f}")

    with open(MODEL_DIR / "results.txt", "w") as f:
        f.write(f"model=YOLOv8s-cls\ntest_accuracy={top1:.6f}\ntest_top5={top5:.6f}\n")

    return top1, top5


def copy_best_model():
    """Move best.pt to a predictable location."""
    src = MODEL_DIR / "train" / "weights" / "best.pt"
    dst = MODEL_DIR / "best.pt"
    if src.exists():
        shutil.copy2(src, dst)
        print(f"[INFO] Best weights copied -> {dst}")
    else:
        print(f"[WARNING] best.pt not found at {src}")


def plot_training_curves():
    """Parse Ultralytics CSV log and plot training curves."""
    csv_path = MODEL_DIR / "train" / "results.csv"
    if not csv_path.exists():
        return

    import pandas as pd
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle("YOLOv8s-cls Training History", fontsize=13)

    # Accuracy columns (top1_acc in ultralytics)
    acc_cols = [c for c in df.columns if "acc" in c.lower() or "top1" in c.lower()]
    loss_cols = [c for c in df.columns if "loss" in c.lower()]

    if acc_cols:
        for col in acc_cols:
            axes[0].plot(df["epoch"] if "epoch" in df.columns else df.index,
                         df[col], label=col)
        axes[0].set_title("Accuracy")
        axes[0].set_xlabel("Epoch")
        axes[0].legend(fontsize=8)
        axes[0].grid(alpha=0.3)

    if loss_cols:
        for col in loss_cols[:3]:    # limit to 3 loss curves
            axes[1].plot(df["epoch"] if "epoch" in df.columns else df.index,
                         df[col], label=col)
        axes[1].set_title("Loss")
        axes[1].set_xlabel("Epoch")
        axes[1].legend(fontsize=8)
        axes[1].grid(alpha=0.3)

    plt.tight_layout()
    out = MODEL_DIR / "training_history.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[INFO] Training curves saved -> {out}")


def main():
    print("=" * 60)
    print("  Crop Disease Pipeline - Step 5: Train YOLOv8")
    print("=" * 60)

    if not YOLO_DIR.exists():
        print(f"[ERROR] YOLO dataset not found at {YOLO_DIR}")
        print("  Run 02_prepare_dataset.py first.")
        raise SystemExit(1)

    class_names = load_class_names()
    print(f"[INFO] {len(class_names)} classes")
    print(f"[INFO] Model  : {YOLO_MODEL}")
    print(f"[INFO] Epochs : {EPOCHS}  |  ImgSz: {IMG_SIZE}  |  Batch: {BATCH_SIZE}")

    model, train_results = train_yolov8()
    top1, top5 = evaluate_yolov8(model, class_names)
    copy_best_model()
    plot_training_curves()

    print("\n[DONE] YOLOv8 training complete.")
    print(f"  Best model    -> {MODEL_DIR}/best.pt")
    print(f"  Test Top-1    -> {top1:.4f}")
    print(f"  Test Top-5    -> {top5:.4f}")


if __name__ == "__main__":
    main()
