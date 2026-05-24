from pathlib import Path
import hashlib
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


app = FastAPI(title="TFLite Model Storage Server")

@app.get("/")
def root():
    return {
        "service": "TFLite Model Storage Server",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "models": "/models"
    }

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models_store"


def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def parse_model_folder_name(folder_name: str) -> dict:
    """
    Пример:
    yolo11n_cls_224e30

    Получаем:
    architecture: yolo11n
    task: cls
    image_size: 224
    epochs: 30
    """

    result = {
        "architecture": None,
        "task": None,
        "image_size": None,
        "epochs": None
    }

    parts = folder_name.split("_")

    if len(parts) >= 1:
        result["architecture"] = parts[0]

    if len(parts) >= 2:
        result["task"] = parts[1]

    match = re.search(r"(\d+)e(\d+)", folder_name)
    if match:
        result["image_size"] = int(match.group(1))
        result["epochs"] = int(match.group(2))

    return result


def make_display_name(folder_name: str) -> str:
    parsed = parse_model_folder_name(folder_name)

    architecture = parsed.get("architecture") or folder_name
    task = parsed.get("task")
    image_size = parsed.get("image_size")
    epochs = parsed.get("epochs")

    parts = [architecture]

    if task:
        if task == "cls":
            parts.append("classification")
        else:
            parts.append(task)

    if image_size:
        parts.append(f"{image_size}x{image_size}")

    if epochs:
        parts.append(f"{epochs} epochs")

    return " / ".join(parts)


def get_available_models() -> list[dict]:
    if not MODEL_DIR.exists():
        return []

    models = []

    for model_folder in sorted(MODEL_DIR.iterdir()):
        if not model_folder.is_dir():
            continue

        tflite_files = sorted(model_folder.glob("*.tflite"))

        if not tflite_files:
            continue

        # Берём первый .tflite файл из папки модели
        model_file = tflite_files[0]

        model_id = model_folder.name
        parsed = parse_model_folder_name(model_id)

        models.append({
            "id": model_id,
            "name": model_id,
            "display_name": make_display_name(model_id),
            "file_name": model_file.name,
            "relative_path": f"{model_id}/{model_file.name}",
            "download_url": f"/models/{model_id}/download",
            "size_bytes": model_file.stat().st_size,
            "size_mb": round(model_file.stat().st_size / 1024 / 1024, 2),
            "sha256": calculate_sha256(model_file),
            "format": "tflite",
            "architecture": parsed["architecture"],
            "task": parsed["task"],
            "image_size": parsed["image_size"],
            "epochs": parsed["epochs"]
        })

    return models


def find_model_by_id(model_id: str) -> dict | None:
    models = get_available_models()

    for model in models:
        if model["id"] == model_id:
            return model

    return None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "model-storage"
    }


@app.get("/models/manifest")
def get_manifest():
    models = get_available_models()

    return {
        "models_count": len(models),
        "models": models
    }


@app.get("/models")
def get_models():
    """
    Короткий список моделей для экрана выбора в мобильном приложении.
    """

    models = get_available_models()

    return {
        "models_count": len(models),
        "models": [
            {
                "id": model["id"],
                "display_name": model["display_name"],
                "size_mb": model["size_mb"],
                "format": model["format"],
                "architecture": model["architecture"],
                "task": model["task"],
                "image_size": model["image_size"],
                "epochs": model["epochs"],
                "download_url": model["download_url"]
            }
            for model in models
        ]
    }


@app.get("/models/{model_id}")
def get_model_info(model_id: str):
    """
    Полная информация по одной модели.
    """

    model = find_model_by_id(model_id)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found"
        )

    return model


@app.get("/models/{model_id}/download")
def download_model(model_id: str):
    """
    Скачивание выбранной пользователем модели.
    """

    model = find_model_by_id(model_id)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found"
        )

    model_file = MODEL_DIR / model["relative_path"]

    if not model_file.exists() or not model_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Model file not found"
        )

    return FileResponse(
        model_file,
        media_type="application/octet-stream",
        filename=f"{model_id}.tflite"
    )