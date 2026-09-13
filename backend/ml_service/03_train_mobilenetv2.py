"""
03_train_mobilenetv2.py
-----------------------
Fine-tunes MobileNetV2 for crop disease classification.

Strategy:
  Phase 1 — Train only the new classifier head (base frozen, 10 epochs)
  Phase 2 — Unfreeze the last 30 layers, fine-tune with low LR (20 epochs)

Saves:
  models/mobilenetv2/best_model.keras
  models/mobilenetv2/training_history.csv
  models/mobilenetv2/confusion_matrix.png
"""

import os
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ── Configuration ────────────────────────────────────────────────────────────
SPLIT_DIR    = Path("data/split")  
MODEL_DIR    = Path("models/mobilenetv2")
CLASS_FILE   = Path("data/class_names.txt")

IMG_SIZE     = (224, 224)
BATCH_SIZE   = 32
PHASE1_EPOCHS = 10
PHASE2_EPOCHS = 20
LEARNING_RATE_HEAD  = 1e-3
LEARNING_RATE_FINETUNE = 1e-5
DROPOUT_RATE = 0.3
UNFREEZE_LAST_N = 30          # layers to unfreeze in phase 2
# ─────────────────────────────────────────────────────────────────────────────

MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_class_names() -> list[str]:
    with open(CLASS_FILE) as f:
        return [line.strip().split("\t")[1] for line in f if line.strip()]


def build_generators():
    train_aug = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=20,
        width_shift_range=0.15,
        height_shift_range=0.15,
        shear_range=0.1,
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode="nearest",
    )
    val_aug = ImageDataGenerator(rescale=1.0 / 255)

    train_gen = train_aug.flow_from_directory(
        SPLIT_DIR / "train",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=True,
        seed=42,
    )
    val_gen = val_aug.flow_from_directory(
        SPLIT_DIR / "val",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )
    test_gen = val_aug.flow_from_directory(
        SPLIT_DIR / "test",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )
    return train_gen, val_gen, test_gen


def build_model(num_classes: int) -> tf.keras.Model:
    base = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False    # Phase 1: frozen

    inputs = layers.Input(shape=(*IMG_SIZE, 3))
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    return models.Model(inputs, outputs), base


def get_callbacks(phase: int) -> list:
    return [
        callbacks.ModelCheckpoint(
            MODEL_DIR / "best_model.keras",
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1,
        ),
        callbacks.CSVLogger(MODEL_DIR / f"history_phase{phase}.csv"),
    ]


def compute_class_weights(train_gen) -> dict:
    """Compute balanced class weights to handle imbalance."""
    from sklearn.utils.class_weight import compute_class_weight
    labels = train_gen.classes
    classes = np.unique(labels)
    weights = compute_class_weight("balanced", classes=classes, y=labels)
    return dict(zip(classes, weights))


def plot_history(history_phase1, history_phase2):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("MobileNetV2 Training History", fontsize=14)

    for ax, metric, title in zip(
        axes,
        ["accuracy", "loss"],
        ["Accuracy", "Loss"],
    ):
        # Phase 1
        ep1 = range(1, len(history_phase1.history[metric]) + 1)
        ax.plot(ep1, history_phase1.history[metric], "b-", label="Train Ph1")
        ax.plot(ep1, history_phase1.history[f"val_{metric}"], "b--", label="Val Ph1")
        # Phase 2
        offset = len(ep1)
        ep2 = range(offset + 1, offset + len(history_phase2.history[metric]) + 1)
        ax.plot(ep2, history_phase2.history[metric], "r-", label="Train Ph2")
        ax.plot(ep2, history_phase2.history[f"val_{metric}"], "r--", label="Val Ph2")
        ax.axvline(x=offset + 0.5, color="gray", linestyle=":", label="Unfreeze")
        ax.set_title(title)
        ax.set_xlabel("Epoch")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(MODEL_DIR / "training_history.png", dpi=150)
    plt.close()
    print(f"[INFO] Training plot saved -> {MODEL_DIR}/training_history.png")


def evaluate_and_save(model, test_gen, class_names):
    from sklearn.metrics import classification_report, confusion_matrix
    import seaborn as sns

    print("[INFO] Evaluating on test set ...")
    test_loss, test_acc = model.evaluate(test_gen, verbose=0)
    print(f"  Test accuracy: {test_acc:.4f}  |  Test loss: {test_loss:.4f}")

    # Predictions
    y_pred = np.argmax(model.predict(test_gen, verbose=0), axis=1)
    y_true = test_gen.classes[:len(y_pred)]

    # Classification report
    report = classification_report(y_true, y_pred, target_names=class_names, digits=4)
    print("\n" + report)
    with open(MODEL_DIR / "classification_report.txt", "w") as f:
        f.write(f"Test Accuracy: {test_acc:.4f}\nTest Loss: {test_loss:.4f}\n\n")
        f.write(report)

    # Confusion matrix (only if ≤ 40 classes to keep it readable)
    if len(class_names) <= 40:
        cm = confusion_matrix(y_true, y_pred)
        fig_h = max(10, len(class_names) * 0.4)
        fig, ax = plt.subplots(figsize=(fig_h, fig_h * 0.8))
        sns.heatmap(
            cm, annot=len(class_names) <= 20,
            fmt="d", cmap="Blues",
            xticklabels=class_names,
            yticklabels=class_names,
            ax=ax,
        )
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"MobileNetV2 Confusion Matrix (Test Acc: {test_acc:.3f})")
        plt.xticks(rotation=45, ha="right", fontsize=7)
        plt.yticks(rotation=0, fontsize=7)
        plt.tight_layout()
        plt.savefig(MODEL_DIR / "confusion_matrix.png", dpi=150)
        plt.close()
        print(f"[INFO] Confusion matrix saved -> {MODEL_DIR}/confusion_matrix.png")

    # Save scalar results for comparison
    with open(MODEL_DIR / "results.txt", "w") as f:
        f.write(f"model=MobileNetV2\ntest_accuracy={test_acc:.6f}\ntest_loss={test_loss:.6f}\n")


def main():
    print("=" * 60)
    print("  Crop Disease Pipeline - Step 3: Train MobileNetV2")
    print("=" * 60)

    # GPU check
    gpus = tf.config.list_physical_devices("GPU")
    print(f"[INFO] GPUs available: {len(gpus)}")
    if gpus:
        tf.config.experimental.set_memory_growth(gpus[0], True)

    class_names = load_class_names()
    num_classes = len(class_names)
    print(f"[INFO] {num_classes} classes loaded from {CLASS_FILE}")

    train_gen, val_gen, test_gen = build_generators()
    class_weights = compute_class_weights(train_gen)
    model, base = build_model(num_classes)

    print(f"\n[PHASE 1] Training classifier head ({PHASE1_EPOCHS} epochs, base frozen)")
    model.compile(
        optimizer=optimizers.Adam(LEARNING_RATE_HEAD),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary(print_fn=lambda x: None)  # suppress full summary
    print(f"  Trainable params: {sum(np.prod(v.shape) for v in model.trainable_variables):,}")

    hist1 = model.fit(
        train_gen,
        epochs=PHASE1_EPOCHS,
        validation_data=val_gen,
        class_weight=class_weights,
        callbacks=get_callbacks(1),
    )

    print(f"\n[PHASE 2] Fine-tuning last {UNFREEZE_LAST_N} layers ({PHASE2_EPOCHS} epochs)")
    base.trainable = True
    for layer in base.layers[:-UNFREEZE_LAST_N]:
        layer.trainable = False

    model.compile(
        optimizer=optimizers.Adam(LEARNING_RATE_FINETUNE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    print(f"  Trainable params: {sum(np.prod(v.shape) for v in model.trainable_variables):,}")

    hist2 = model.fit(
        train_gen,
        epochs=PHASE2_EPOCHS,
        validation_data=val_gen,
        class_weight=class_weights,
        callbacks=get_callbacks(2),
    )

    # Load best weights
    model.load_weights(MODEL_DIR / "best_model.keras")

    plot_history(hist1, hist2)
    evaluate_and_save(model, test_gen, class_names)

    print("\n[DONE] MobileNetV2 training complete.")
    print(f"  Best model saved to {MODEL_DIR}/best_model.keras")


if __name__ == "__main__":
    main()
