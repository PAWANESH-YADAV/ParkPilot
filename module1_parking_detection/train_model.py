"""
ParkPilot — Module 1: Parking Space Detection Model Training
Trains a CNN (MobileNetV2 transfer learning) classifier on the PKLot dataset
to distinguish VACANT vs OCCUPIED parking slots.

Dataset: PKLot — https://web.inf.ufpr.br/vri/databases/parking-lot-database/
         Download and extract to: data/PKLot/

Usage:
    python module1_parking_detection/train_model.py
"""

import os
import sys
import numpy as np
import pickle
import matplotlib.pyplot as plt
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger("parkpilot.module1.train")

# ─── Check TensorFlow / Keras availability ───────────────────────────────────
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
    TF_AVAILABLE = True
    logger.info(f"TensorFlow {tf.__version__} loaded")
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed — using sklearn SVM fallback")

try:
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.pipeline import Pipeline
    import cv2
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.error("scikit-learn and OpenCV required. Install with: pip install scikit-learn opencv-python")


# ─── Configuration ───────────────────────────────────────────────────────────
IMG_SIZE = (64, 64)             # Resize each slot crop to 64x64
BATCH_SIZE = 32
EPOCHS = 30
LEARNING_RATE = 1e-4
DATA_DIR = "data/PKLot"         # Root of extracted PKLot dataset
MODEL_OUTPUT = "module1_parking_detection/model.h5"
MODEL_PKL_OUTPUT = "module1_parking_detection/model_svm.pkl"
CLASS_NAMES = ["occupied", "vacant"]  # 0 = occupied, 1 = vacant


# ═══════════════════════════════════════════════════════════════════════════
#  OPTION A — CNN with MobileNetV2 Transfer Learning (Recommended)
# ═══════════════════════════════════════════════════════════════════════════

def build_mobilenet_model(input_shape=(64, 64, 3), num_classes=2) -> "tf.keras.Model":
    """
    Build a binary classifier using MobileNetV2 as the backbone.
    Freezes pre-trained weights and adds custom classification head.

    Returns:
        Compiled Keras model
    """
    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet"
    )
    # Freeze base model weights for transfer learning
    base_model.trainable = False

    inputs = keras.Input(shape=input_shape)
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.4)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = keras.Model(inputs, outputs, name="ParkPilot_MobileNetV2")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    logger.info(f"MobileNetV2 model built: {model.count_params():,} parameters")
    return model


def build_custom_cnn(input_shape=(64, 64, 3)) -> "tf.keras.Model":
    """
    Lightweight custom CNN for lower-resource environments.
    ~3.5x faster than MobileNetV2 with slightly lower accuracy.
    """
    model = keras.Sequential([
        keras.Input(shape=input_shape),
        layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(2, 2),

        layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(2, 2),

        layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(2, 2),

        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.5),
        layers.Dense(2, activation="softmax")
    ], name="ParkPilot_CNN")

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model


def create_data_generators(data_dir: str):
    """
    Create ImageDataGenerator for training and validation.
    Applies augmentation: flip, zoom, shift, brightness change.

    PKLot directory structure expected:
        data/PKLot/
            train/
                occupied/  (images of occupied slots)
                vacant/    (images of vacant slots)
            validation/
                occupied/
                vacant/
    """
    train_gen = ImageDataGenerator(
        rescale=1.0 / 255,
        horizontal_flip=True,
        vertical_flip=False,
        zoom_range=0.15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        brightness_range=[0.5, 1.5],    # Simulate day/night conditions
        rotation_range=10,
        fill_mode="nearest"
    )

    val_gen = ImageDataGenerator(rescale=1.0 / 255)

    train_data = train_gen.flow_from_directory(
        os.path.join(data_dir, "train"),
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        classes=CLASS_NAMES,
        shuffle=True
    )

    val_data = val_gen.flow_from_directory(
        os.path.join(data_dir, "validation"),
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        classes=CLASS_NAMES,
        shuffle=False
    )

    logger.info(f"Training samples: {train_data.n}")
    logger.info(f"Validation samples: {val_data.n}")
    return train_data, val_data


def train_cnn_model(use_mobilenet: bool = True, data_dir: str = DATA_DIR):
    """
    Train the CNN model on PKLot dataset.

    Args:
        use_mobilenet: If True, use MobileNetV2 (recommended). Else use custom CNN.
        data_dir: Path to PKLot dataset root directory
    """
    if not TF_AVAILABLE:
        logger.error("TensorFlow required for CNN training")
        return None

    if not os.path.exists(data_dir):
        logger.error(
            f"Dataset not found at: {data_dir}\n"
            "Download PKLot from: https://web.inf.ufpr.br/vri/databases/parking-lot-database/"
        )
        return None

    logger.info("Starting CNN training on PKLot dataset...")
    train_data, val_data = create_data_generators(data_dir)

    # Build model
    model = build_mobilenet_model() if use_mobilenet else build_custom_cnn()
    model.summary()

    # Callbacks
    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    callbacks = [
        ModelCheckpoint(
            MODEL_OUTPUT,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1
        ),
        EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        )
    ]

    # Phase 1: Train with frozen base (transfer learning warm-up)
    logger.info("Phase 1: Training classification head (base frozen)...")
    history = model.fit(
        train_data,
        validation_data=val_data,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )

    if use_mobilenet:
        # Phase 2: Fine-tune — unfreeze last 20 layers of MobileNetV2
        logger.info("Phase 2: Fine-tuning last 20 layers...")
        base = model.layers[1]
        base.trainable = True
        for layer in base.layers[:-20]:
            layer.trainable = False

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-5),
            loss="categorical_crossentropy",
            metrics=["accuracy"]
        )
        model.fit(
            train_data,
            validation_data=val_data,
            epochs=10,
            callbacks=callbacks,
            verbose=1
        )

    # Evaluate
    val_loss, val_acc = model.evaluate(val_data, verbose=0)
    logger.info(f"✅ Training complete | Val Accuracy: {val_acc:.4f} | Val Loss: {val_loss:.4f}")

    # Plot training history
    _plot_training_history(history)

    model.save(MODEL_OUTPUT)
    logger.info(f"Model saved to: {MODEL_OUTPUT}")
    return model


def _plot_training_history(history):
    """Plot and save accuracy/loss curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    ax1.plot(history.history["accuracy"], label="Train Accuracy")
    ax1.plot(history.history["val_accuracy"], label="Val Accuracy")
    ax1.set_title("Model Accuracy")
    ax1.set_xlabel("Epoch")
    ax1.legend()

    ax2.plot(history.history["loss"], label="Train Loss")
    ax2.plot(history.history["val_loss"], label="Val Loss")
    ax2.set_title("Model Loss")
    ax2.set_xlabel("Epoch")
    ax2.legend()

    plt.tight_layout()
    os.makedirs("module1_parking_detection", exist_ok=True)
    plt.savefig("module1_parking_detection/training_history.png", dpi=100)
    plt.close()
    logger.info("Training history plot saved")


# ═══════════════════════════════════════════════════════════════════════════
#  OPTION B — SVM on HOG Features (Lightweight Fallback)
# ═══════════════════════════════════════════════════════════════════════════

def extract_hog_features(image: np.ndarray) -> np.ndarray:
    """
    Extract HOG (Histogram of Oriented Gradients) features from a slot image.
    Used as input features for the SVM classifier.

    Args:
        image: BGR image (any size — will be resized to 64x64)

    Returns:
        HOG feature vector
    """
    resized = cv2.resize(image, IMG_SIZE)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    win_size = (64, 64)
    block_size = (16, 16)
    block_stride = (8, 8)
    cell_size = (8, 8)
    nbins = 9

    hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
    features = hog.compute(gray)
    return features.flatten()


def load_dataset_for_svm(data_dir: str):
    """
    Load PKLot images and extract HOG features for SVM training.

    Returns:
        X: Feature matrix, y: Labels
    """
    X, y = [], []
    for label_idx, class_name in enumerate(CLASS_NAMES):
        for split in ["train", "validation"]:
            folder = os.path.join(data_dir, split, class_name)
            if not os.path.exists(folder):
                continue
            for img_file in Path(folder).glob("*.jpg"):
                img = cv2.imread(str(img_file))
                if img is None:
                    continue
                features = extract_hog_features(img)
                X.append(features)
                y.append(label_idx)

    logger.info(f"Loaded {len(X)} samples for SVM training")
    return np.array(X), np.array(y)


def train_svm_model(data_dir: str = DATA_DIR):
    """
    Train an SVM classifier on HOG features extracted from PKLot dataset.
    Faster to train and run than CNN — suitable for low-resource systems.
    """
    if not SKLEARN_AVAILABLE:
        logger.error("scikit-learn required")
        return None

    logger.info("Loading dataset for SVM training...")
    X, y = load_dataset_for_svm(data_dir)

    if len(X) == 0:
        logger.error("No training data found")
        return None

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, random_state=42))
    ])

    logger.info("Training SVM...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info(f"✅ SVM Accuracy: {acc:.4f}")
    logger.info("\n" + classification_report(y_test, y_pred, target_names=CLASS_NAMES))

    os.makedirs("module1_parking_detection", exist_ok=True)
    with open(MODEL_PKL_OUTPUT, "wb") as f:
        pickle.dump(pipeline, f)
    logger.info(f"SVM model saved to: {MODEL_PKL_OUTPUT}")

    return pipeline


# ═══════════════════════════════════════════════════════════════════════════
#  Slot Position Saver
# ═══════════════════════════════════════════════════════════════════════════

def save_demo_slot_positions(num_slots: int = 50, cols: int = 10):
    """
    Generate and save demo slot positions for a synthetic parking lot grid.
    In a real deployment, use the interactive slot definer tool.

    Args:
        num_slots: Total number of slots
        cols: Columns per row
    """
    slot_width, slot_height = 80, 40
    margin_x, margin_y = 10, 10
    start_x, start_y = 50, 80

    slot_positions = []
    for i in range(num_slots):
        row = i // cols
        col = i % cols
        x = start_x + col * (slot_width + margin_x)
        y = start_y + row * (slot_height + margin_y)
        slot_positions.append({
            "id": i + 1,
            "x": x,
            "y": y,
            "width": slot_width,
            "height": slot_height,
            "zone": "A" if row < 3 else ("B" if row < 6 else "C"),
            "level": 1
        })

    os.makedirs("module1_parking_detection", exist_ok=True)
    with open("module1_parking_detection/slot_positions.pkl", "wb") as f:
        pickle.dump(slot_positions, f)
    logger.info(f"Saved {num_slots} demo slot positions")
    return slot_positions


# ═══════════════════════════════════════════════════════════════════════════
#  Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ParkPilot — Module 1: Train Parking Detection Model")
    parser.add_argument("--mode", choices=["cnn", "svm", "positions"], default="cnn",
                        help="Training mode: 'cnn' (MobileNetV2), 'svm' (HOG+SVM), 'positions' (generate demo positions)")
    parser.add_argument("--data-dir", default=DATA_DIR, help="Path to PKLot dataset")
    parser.add_argument("--mobilenet", action="store_true", default=True,
                        help="Use MobileNetV2 backbone (CNN mode only)")
    parser.add_argument("--slots", type=int, default=50, help="Number of demo slots")
    args = parser.parse_args()

    if args.mode == "cnn":
        train_cnn_model(use_mobilenet=args.mobilenet, data_dir=args.data_dir)
    elif args.mode == "svm":
        train_svm_model(data_dir=args.data_dir)
    elif args.mode == "positions":
        positions = save_demo_slot_positions(num_slots=args.slots)
        print(f"Generated {len(positions)} slot positions → module1_parking_detection/slot_positions.pkl")
