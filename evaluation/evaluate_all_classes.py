"""Evaluate the active YOLO classifier on the complete 22-class test split."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


REPO_ROOT = Path(__file__).resolve().parents[1]
ML_SERVICE_ROOT = REPO_ROOT / "backend" / "ml_service"
if str(ML_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_SERVICE_ROOT))

from app.model import DiseasePredictor  # noqa: E402


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def crop_name(class_name: str) -> str:
    return "Tomato" if class_name.startswith("Tomato") else class_name.split()[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=REPO_ROOT / "data" / "yolo" / "test",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "evaluation" / "all_classes",
    )
    parser.add_argument("--model", type=Path, default=None)
    return parser.parse_args()


def collect_samples(dataset_root: Path, class_names: list[str]) -> list[tuple[str, Path]]:
    directory_names = {
        path.name for path in dataset_root.iterdir() if path.is_dir()
    }
    expected_names = set(class_names)
    missing = sorted(expected_names - directory_names)
    unexpected = sorted(directory_names - expected_names)
    if missing or unexpected:
        raise RuntimeError(
            "Dataset/model class mismatch. "
            f"Missing directories: {missing or 'none'}; "
            f"unexpected directories: {unexpected or 'none'}."
        )

    samples: list[tuple[str, Path]] = []
    for class_name in class_names:
        images = sorted(
            path
            for path in (dataset_root / class_name).rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        if not images:
            raise RuntimeError(f"No test images found for {class_name}")
        samples.extend((class_name, path) for path in images)
    return samples


def calculate_per_class_metrics(
    predictions: pd.DataFrame, class_names: list[str]
) -> pd.DataFrame:
    precision, recall, f1, support = precision_recall_fscore_support(
        predictions["actual_class"],
        predictions["predicted_class"],
        labels=class_names,
        zero_division=0,
    )
    rows = []
    for index, class_name in enumerate(class_names):
        actual = predictions["actual_class"] == class_name
        predicted = predictions["predicted_class"] == class_name
        rows.append(
            {
                "class": class_name,
                "crop": crop_name(class_name),
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "false_negative_rate": float(1.0 - recall[index]),
                "true_positive": int((actual & predicted).sum()),
                "false_positive": int((~actual & predicted).sum()),
                "false_negative": int((actual & ~predicted).sum()),
                "support": int(support[index]),
            }
        )
    return pd.DataFrame(rows)


def save_confusion_matrices(
    matrix: np.ndarray, class_names: list[str], output_dir: Path
) -> None:
    short_names = [
        name.replace("Tomato_", "Tomato ").replace("Cashew ", "C. ")
        .replace("Cassava ", "Ca. ").replace("Maize ", "M. ")
        .replace("Tomato ", "T. ")
        for name in class_names
    ]
    normalized = matrix.astype(float) / np.maximum(matrix.sum(axis=1, keepdims=True), 1)

    for values, filename, title, fmt, size in (
        (matrix, "confusion_matrix.png", "22-class confusion matrix (counts)", "d", (18, 15)),
        (
            normalized,
            "confusion_matrix_normalized.png",
            "22-class confusion matrix (row-normalized)",
            ".0%",
            (18, 15),
        ),
    ):
        plt.figure(figsize=size)
        sns.heatmap(
            values,
            annot=True,
            fmt=fmt,
            cmap="Blues",
            xticklabels=short_names,
            yticklabels=short_names,
            vmin=0 if values is normalized else None,
            vmax=1 if values is normalized else None,
            annot_kws={"fontsize": 7},
        )
        plt.title(title)
        plt.xlabel("Predicted class")
        plt.ylabel("Actual class")
        plt.xticks(rotation=55, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(output_dir / filename, dpi=180)
        plt.close()


def main() -> None:
    args = parse_args()
    dataset_root = args.dataset_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    predictor = DiseasePredictor(
        model_path=str(args.model.resolve()) if args.model else None
    )
    class_names = list(predictor.class_names)
    if len(class_names) != 22:
        raise RuntimeError(f"Expected 22 model classes, found {len(class_names)}")

    samples = collect_samples(dataset_root, class_names)
    records = []
    print(f"Evaluating {len(samples)} images across {len(class_names)} classes")

    for number, (actual_class, image_path) in enumerate(samples, start=1):
        started = time.perf_counter()
        with Image.open(image_path) as image:
            result = predictor.predict(image.convert("RGB"))
        records.append(
            {
                "image_path": image_path.relative_to(dataset_root).as_posix(),
                "actual_class": actual_class,
                "predicted_class": result["disease_name"],
                "confidence": float(result["confidence"]),
                "correct": result["disease_name"] == actual_class,
                "latency_ms": (time.perf_counter() - started) * 1000,
            }
        )
        if number % 250 == 0 or number == len(samples):
            print(f"Processed {number}/{len(samples)} images", flush=True)

    predictions = pd.DataFrame(records)
    metrics = calculate_per_class_metrics(predictions, class_names)
    matrix = confusion_matrix(
        predictions["actual_class"],
        predictions["predicted_class"],
        labels=class_names,
    )
    matrix_frame = pd.DataFrame(
        matrix,
        index=pd.Index(class_names, name="actual_class"),
        columns=pd.Index(class_names, name="predicted_class"),
    )

    crop_metrics = (
        predictions.assign(crop=predictions["actual_class"].map(crop_name))
        .groupby("crop", as_index=False)
        .agg(
            total_images=("correct", "size"),
            correct_predictions=("correct", "sum"),
            accuracy=("correct", "mean"),
        )
    )

    predictions.to_csv(output_dir / "predictions.csv", index=False)
    metrics.to_csv(
        output_dir / "per_class_metrics.csv", index=False, float_format="%.6f"
    )
    crop_metrics.to_csv(
        output_dir / "per_crop_metrics.csv", index=False, float_format="%.6f"
    )
    matrix_frame.to_csv(output_dir / "confusion_matrix.csv")
    save_confusion_matrices(matrix, class_names, output_dir)

    weights = metrics["support"].to_numpy(dtype=float)
    summary = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_root": str(dataset_root),
        "model_path": str(predictor.model_path),
        "number_of_classes": len(class_names),
        "total_images": int(len(predictions)),
        "correct_predictions": int(predictions["correct"].sum()),
        "overall_accuracy": float(predictions["correct"].mean()),
        "macro_precision": float(metrics["precision"].mean()),
        "macro_recall": float(metrics["recall"].mean()),
        "macro_f1": float(metrics["f1"].mean()),
        "weighted_f1": float(np.average(metrics["f1"], weights=weights)),
        "mean_latency_ms": float(predictions["latency_ms"].mean()),
        "p95_latency_ms": float(predictions["latency_ms"].quantile(0.95)),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("\nPer-class metrics")
    print(metrics.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print("\nPer-crop metrics")
    print(crop_metrics.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print("\nSummary")
    print(json.dumps(summary, indent=2))
    print(f"\nArtifacts saved to {output_dir}")


if __name__ == "__main__":
    main()
