"""
04_train_efficientnet.py
------------------------
Fine-tunes EfficientNetB0 for crop disease classification.

EfficientNet uses its own preprocessing (no rescaling to [0,1] needed —
it expects raw [0,255] uint8 and applies its own normalization internally).

Strategy (same two-phase as MobileNetV2):
  Phase 1 — Classifier head only, 10 epochs
  Phase 2 — Unfreeze top layers + fine-tune, 20 epochs

Saves:
  models/efficientnet/best_model.keras
  models/efficientnet/training_history.png
  models/efficientnet/classification_report.txt
  models/efficientnet/results.txt
"""

import os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ── Configuration ────────────────────────────────────────────────────────────
SPLIT_DIR   = Path("data/split")
MODEL_DIR   = Path("models/efficientnet")
CLASS_FILE  = Path("data/class_names.txt")

IMG_SIZE    = (224, 224)
BATCH_SIZE  = 32
PHASE1_EPOCHS  = 10
PHASE2_EPOCHS  = 25
LR_HEAD        = 1e-3
LR_FINETUNE    = 5e-6
DROPOUT_RATE   = 0.4
UNFREEZE_LAST_N = 40
# ─────────────────────────────────────────────────────────────────────────────

MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_class_names() -> list[str]:
    with open(CLASS_FILE) as f:
        return [line.strip().split("\t")[1] for line in f if line.strip()]


def build_generators():
    """
    EfficientNet expects pixel values in [0, 255] — the preprocessing layer
    inside the model handles normalization. So we DO NOT rescale here.
    """
    train_aug = ImageDataGenerator(
        rotation_range=25,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.2,
        horizontal_flip=True,
        vertical_flip=False,
        brightness_range=[0.7, 1.3],
        fill_mode="nearest",
        # No rescale — EfficientNet preprocesses internally
    )
    val_aug = ImageDataGenerator()   # no augmentation, no rescale

    kw = dict(target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode="categorical")
    train_gen = train_aug.flow_from_directory(SPLIT_DIR / "train", shuffle=True,  seed=42, **kw)
    val_gen   = val_aug.flow_from_directory(SPLIT_DIR / "val",   shuffle=False, **kw)
    test_gen  = val_aug.flow_from_directory(SPLIT_DIR / "test",  shuffle=False, **kw)
    return train_gen, val_gen, test_gen


def build_model(num_classes: int):
    base = EfficientNetB0(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    inputs = layers.Input(shape=(*IMG_SIZE, 3))
    # EfficientNet's built-in preprocessing handles normalization
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(512, activation="relu")(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(DROPOUT_RATE * 0.5)(x)
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
            patience=6,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.4,
            patience=3,
            min_lr=1e-8,
            verbose=1,
        ),
        callbacks.CSVLogger(MODEL_DIR / f"history_phase{phase}.csv"),
    ]


def compute_class_weights(train_gen) -> dict:
    from sklearn.utils.class_weight import compute_class_weight
    labels = train_gen.classes
    classes = np.unique(labels)
    weights = compute_class_weight("balanced", classes=classes, y=labels)
    return dict(zip(classes, weights))


def plot_history(h1, h2, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("EfficientNetB0 Training History", fontsize=14)
    for ax, metric, title in zip(axes, ["accuracy", "loss"], ["Accuracy", "Loss"]):
        e1 = range(1, len(h1.history[metric]) + 1)
        ax.plot(e1, h1.history[metric],           "b-",  label="Train Ph1")
        ax.plot(e1, h1.history[f"val_{metric}"],  "b--", label="Val Ph1")
        offset = len(e1)
        e2 = range(offset + 1, offset + len(h2.history[metric]) + 1)
        ax.plot(e2, h2.history[metric],           "r-",  label="Train Ph2")
        ax.plot(e2, h2.history[f"val_{metric}"],  "r--", label="Val Ph2")
        ax.axvline(x=offset + 0.5, color="gray", linestyle=":", label="Unfreeze")
        ax.set_title(title)
        ax.set_xlabel("Epoch")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def evaluate_and_save(model, test_gen, class_names):
    from sklearn.metrics import classification_report, confusion_matrix
    import seaborn as sns

    print("[INFO] Evaluating on test set ...")
    test_loss, test_acc = model.evaluate(test_gen, verbose=0)
    print(f"  Test accuracy: {test_acc:.4f}  |  Test loss: {test_loss:.4f}")

    y_pred = np.argmax(model.predict(test_gen, verbose=0), axis=1)
    y_true = test_gen.classes[:len(y_pred)]

    report = classification_report(y_true, y_pred, target_names=class_names, digits=4)
    print("\n" + report)
    with open(MODEL_DIR / "classification_report.txt", "w") as f:
        f.write(f"Test Accuracy: {test_acc:.4f}\nTest Loss: {test_loss:.4f}\n\n{report}")

    if len(class_names) <= 40:
        cm = confusion_matrix(y_true, y_pred)
        fig_h = max(10, len(class_names) * 0.4)
        fig, ax = plt.subplots(figsize=(fig_h, fig_h * 0.8))
        sns.heatmap(cm, annot=len(class_names) <= 20, fmt="d", cmap="Greens",
                    xticklabels=class_names, yticklabels=class_names, ax=ax)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"EfficientNetB0 Confusion Matrix (Test Acc: {test_acc:.3f})")
        plt.xticks(rotation=45, ha="right", fontsize=7)
        plt.yticks(rotation=0, fontsize=7)
        plt.tight_layout()
        plt.savefig(MODEL_DIR / "confusion_matrix.png", dpi=150)
        plt.close()

    with open(MODEL_DIR / "results.txt", "w") as f:
        f.write(f"model=EfficientNetB0\ntest_accuracy={test_acc:.6f}\ntest_loss={test_loss:.6f}\n")


def main():
    print("=" * 60)
    print("  Crop Disease Pipeline - Step 4: Train EfficientNetB0")
    print("=" * 60)

    gpus = tf.config.list_physical_devices("GPU")
    print(f"[INFO] GPUs available: {len(gpus)}")
    if gpus:
        tf.config.experimental.set_memory_growth(gpus[0], True)

    class_names = load_class_names()
    num_classes = len(class_names)
    print(f"[INFO] {num_classes} classes")

    train_gen, val_gen, test_gen = build_generators()
    class_weights = compute_class_weights(train_gen)
    model, base = build_model(num_classes)

    print(f"\n[PHASE 1] Classifier head only ({PHASE1_EPOCHS} epochs)")
    model.compile(
        optimizer=optimizers.Adam(LR_HEAD),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    hist1 = model.fit(
        train_gen, epochs=PHASE1_EPOCHS,
        validation_data=val_gen,
        class_weight=class_weights,
        callbacks=get_callbacks(1),
    )

    print(f"\n[PHASE 2] Unfreeze top {UNFREEZE_LAST_N} layers ({PHASE2_EPOCHS} epochs)")
    base.trainable = True
    for layer in base.layers[:-UNFREEZE_LAST_N]:
        layer.trainable = False

    model.compile(
        optimizer=optimizers.Adam(LR_FINETUNE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    hist2 = model.fit(
        train_gen, epochs=PHASE2_EPOCHS,
        validation_data=val_gen,
        class_weight=class_weights,
        callbacks=get_callbacks(2),
    )

    model.load_weights(MODEL_DIR / "best_model.keras")
    plot_history(hist1, hist2, MODEL_DIR / "training_history.png")
    evaluate_and_save(model, test_gen, class_names)

    print("\n[DONE] EfficientNetB0 training complete.")
    print(f"  Best model -> {MODEL_DIR}/best_model.keras")


if __name__ == "__main__":
    main()
