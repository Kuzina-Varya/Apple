# Apple Model Storage Server

Серверная часть для хранения и отдачи `.tflite` моделей приложения распознавания яблок.

Проект реализует REST API, через которое мобильное приложение на ОС Аврора получает список доступных моделей, пользователь выбирает нужную модель, после чего приложение скачивает выбранный `.tflite` файл и сохраняет его локально на устройстве.

## Назначение

Сервер отвечает за:

- хранение моделей на серверной стороне;
- формирование списка доступных моделей;
- выдачу полной информации по выбранной модели;
- скачивание выбранной `.tflite` модели;
- проверку доступности сервиса;
- демонстрацию работы через Docker и ngrok.

## Архитектура

```text
ОС Аврора приложение
        ↓ HTTPS
ngrok public URL
        ↓
Docker-контейнер с FastAPI
        ↓
models_store/
        ↓
.tflite модели
```

Для демонстрации сервер запускается локально в Docker, а наружу публикуется через статический ngrok-домен:

```text
https://ninja-primp-late.ngrok-free.dev
```

В промышленном варианте этот же сервер может быть перенесён на VPS или облачный сервер без изменения API.

## Структура проекта

```text
model_server/
 ├── main.py
 ├── requirements.txt
 ├── Dockerfile
 ├── docker-compose.yml
 ├── start_demo.bat
 ├── README.md
 └── models_store/
     ├── yolo11n_cls_224e30/
     │   └── best_float32.tflite
     ├── yolo11n_cls_256e25/
     │   └── best_float32.tflite
     └── yolo11s_cls_224e30/
         └── best_float32.tflite
```

## Модели

На текущем этапе доступны 3 модели:

| ID модели | Описание | Размер |
|---|---|---:|
| `yolo11n_cls_224e30` | YOLO11n, classification, вход 224x224, 30 эпох | ~5.88 MB |
| `yolo11n_cls_256e25` | YOLO11n, classification, вход 256x256, 25 эпох | ~5.88 MB |
| `yolo11s_cls_224e30` | YOLO11s, classification, вход 224x224, 30 эпох | ~20.79 MB |

## Запуск через Docker

Перед запуском должен быть открыт Docker Desktop.

Из папки проекта:

```cmd
docker compose up -d --build
```

Проверить контейнер:

```cmd
docker ps
```

Проверить API локально:

```cmd
curl.exe http://localhost:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "service": "model-storage"
}
```

## Запуск одной командой

Используется файл:

```text
start_demo.bat
```

Он автоматически:

1. проверяет Docker;
2. запускает `docker compose up -d --build`;
3. проверяет локальный API;
4. запускает ngrok на домене `ninja-primp-late.ngrok-free.dev`;
5. выводит ссылки для демонстрации.

Запуск:

```cmd
start_demo.bat
```

Остановка:

```cmd
start_demo.bat stop
```

## API endpoints

### Проверка сервера

```http
GET /health
```

Пример:

```text
https://ninja-primp-late.ngrok-free.dev/health
```

Ответ:

```json
{
  "status": "ok",
  "service": "model-storage"
}
```

### Главная информация

```http
GET /
```

Ответ содержит служебную информацию и ссылки на основные endpoint'ы.

### Получить список моделей

```http
GET /models
```

Пример:

```text
https://ninja-primp-late.ngrok-free.dev/models
```

Пример ответа:

```json
{
  "models_count": 3,
  "models": [
    {
      "id": "yolo11n_cls_224e30",
      "display_name": "yolo11n / classification / 224x224 / 30 epochs",
      "size_mb": 5.88,
      "format": "tflite",
      "architecture": "yolo11n",
      "task": "cls",
      "image_size": 224,
      "epochs": 30,
      "download_url": "/models/yolo11n_cls_224e30/download"
    }
  ]
}
```

### Получить полную информацию по модели

```http
GET /models/{model_id}
```

Пример:

```text
https://ninja-primp-late.ngrok-free.dev/models/yolo11n_cls_224e30
```

Ответ содержит:

- `id`;
- `display_name`;
- `file_name`;
- `relative_path`;
- `download_url`;
- `size_bytes`;
- `size_mb`;
- `sha256`;
- `format`;
- `architecture`;
- `task`;
- `image_size`;
- `epochs`.

### Скачать выбранную модель

```http
GET /models/{model_id}/download
```

Пример:

```text
https://ninja-primp-late.ngrok-free.dev/models/yolo11n_cls_224e30/download
```

Ответ:

```text
.tflite файл
```

Тип ответа:

```text
application/octet-stream
```

## Важный header для ngrok

Так как используется бесплатный ngrok-домен, для API-запросов нужно добавлять header:

```http
ngrok-skip-browser-warning: 1
```

Пример проверки через PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "https://ninja-primp-late.ngrok-free.dev/models" `
  -Headers @{ "ngrok-skip-browser-warning" = "1" } | ConvertTo-Json -Depth 10
```

## Проверка скачивания модели

```powershell
Invoke-WebRequest `
  -Uri "https://ninja-primp-late.ngrok-free.dev/models/yolo11n_cls_224e30/download" `
  -Headers @{ "ngrok-skip-browser-warning" = "1" } `
  -OutFile ".\test_yolo11n_cls_224e30.tflite"
```

Проверка размера:

```powershell
(Get-Item .\test_yolo11n_cls_224e30.tflite).Length / 1MB
```

Проверка SHA256:

```powershell
Get-FileHash .\test_yolo11n_cls_224e30.tflite -Algorithm SHA256
```

Хеш должен совпадать со значением `sha256`, полученным из:

```http
GET /models/{model_id}
```




