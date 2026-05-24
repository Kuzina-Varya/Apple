# Инструкция для разработчика приложения на ОС Аврора

Документ описывает, как мобильному приложению на ОС Аврора получать список моделей с сервера, скачивать выбранную `.tflite` модель и сохранять её локально для дальнейшего запуска через TensorFlow Lite.

## Base URL

Для демонстрации используется постоянный ngrok-домен:

```text
https://ninja-primp-late.ngrok-free.dev
```

В коде приложения лучше хранить его как отдельную константу:

```text
baseUrl = "https://ninja-primp-late.ngrok-free.dev"
```

## Важный header для ngrok

Для всех запросов к ngrok-домену нужно добавлять header:

```http
ngrok-skip-browser-warning: 1
```

Без этого на бесплатном ngrok-домене может вернуться HTML-страница предупреждения вместо JSON/API-ответа.

## Основная логика приложения

```text
1. Открывается экран выбора модели.
2. Приложение делает GET /models.
3. Пользователю показывается список моделей.
4. Пользователь выбирает модель.
5. Приложение делает GET /models/{model_id}.
6. Приложение получает size_bytes и sha256.
7. Приложение скачивает GET /models/{model_id}/download.
8. Файл сохраняется в локальное хранилище приложения.
9. Приложение проверяет размер и SHA256.
10. Если проверка прошла, модель становится активной.
11. TensorFlow Lite открывает локальный .tflite файл.
```

## Endpoints

### Проверка сервера

```http
GET /health
```

Полный URL:

```text
https://ninja-primp-late.ngrok-free.dev/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "service": "model-storage"
}
```

### Получить список моделей

```http
GET /models
```

Полный URL:

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
    },
    {
      "id": "yolo11n_cls_256e25",
      "display_name": "yolo11n / classification / 256x256 / 25 epochs",
      "size_mb": 5.88,
      "format": "tflite",
      "architecture": "yolo11n",
      "task": "cls",
      "image_size": 256,
      "epochs": 25,
      "download_url": "/models/yolo11n_cls_256e25/download"
    },
    {
      "id": "yolo11s_cls_224e30",
      "display_name": "yolo11s / classification / 224x224 / 30 epochs",
      "size_mb": 20.79,
      "format": "tflite",
      "architecture": "yolo11s",
      "task": "cls",
      "image_size": 224,
      "epochs": 30,
      "download_url": "/models/yolo11s_cls_224e30/download"
    }
  ]
}
```

Для экрана выбора рекомендуется показывать:

- `display_name`;
- `size_mb`;
- `image_size`;
- при необходимости `architecture`.

### Получить полную информацию по модели

```http
GET /models/{model_id}
```

Пример:

```text
https://ninja-primp-late.ngrok-free.dev/models/yolo11n_cls_224e30
```

Ответ содержит:

```json
{
  "id": "yolo11n_cls_224e30",
  "name": "yolo11n_cls_224e30",
  "display_name": "yolo11n / classification / 224x224 / 30 epochs",
  "file_name": "best_float32.tflite",
  "relative_path": "yolo11n_cls_224e30/best_float32.tflite",
  "download_url": "/models/yolo11n_cls_224e30/download",
  "size_bytes": 6164673,
  "size_mb": 5.88,
  "sha256": "6f7cda785d2301554ebcb2d0d0b72f9237ab1a1b7cd761db0a90ff64ea07c4ce",
  "format": "tflite",
  "architecture": "yolo11n",
  "task": "cls",
  "image_size": 224,
  "epochs": 30
}
```

Важно использовать:

- `size_bytes` — для проверки размера после скачивания;
- `sha256` — для проверки целостности файла;
- `image_size` — для подготовки изображения перед подачей в модель;
- `download_url` — для скачивания выбранной модели.

### Скачать выбранную модель

```http
GET /models/{model_id}/download
```

Пример:

```text
https://ninja-primp-late.ngrok-free.dev/models/yolo11n_cls_224e30/download
```

Ответ — бинарный `.tflite` файл.

Тип ответа:

```http
Content-Type: application/octet-stream
```

Файл будет отдаваться с именем:

```text
{model_id}.tflite
```

Например:

```text
yolo11n_cls_224e30.tflite
```

## Как склеивать URL

В `/models` поле `download_url` приходит относительным:

```text
/models/yolo11n_cls_224e30/download
```

Его нужно склеить с `baseUrl`:

```text
baseUrl + download_url
```

Пример:

```text
https://ninja-primp-late.ngrok-free.dev/models/yolo11n_cls_224e30/download
```

## Рекомендованное локальное хранение на устройстве

Скачанную модель нужно сохранять в локальное хранилище приложения, например:

```text
AppDataLocation/models/yolo11n_cls_224e30.tflite
```

Нельзя каждый раз скачивать модель заново, если она уже есть и прошла проверку.

Рекомендуется локально хранить информацию об активной модели:

```json
{
  "selected_model_id": "yolo11n_cls_224e30",
  "local_path": "AppDataLocation/models/yolo11n_cls_224e30.tflite",
  "sha256": "6f7cda785d2301554ebcb2d0d0b72f9237ab1a1b7cd761db0a90ff64ea07c4ce",
  "size_bytes": 6164673,
  "image_size": 224,
  "downloaded_at": "2026-05-24T12:00:00"
}
```

## Проверка после скачивания

После скачивания файла нужно проверить:

```text
1. Размер локального файла == size_bytes с сервера.
2. SHA256 локального файла == sha256 с сервера.
```

Если проверка не прошла:

```text
1. Удалить повреждённый файл.
2. Показать пользователю ошибку.
3. Предложить повторить скачивание.
```

## Пример логики для Qt/C++

### Получение списка моделей

```cpp
QNetworkAccessManager *manager = new QNetworkAccessManager(this);

QUrl url("https://ninja-primp-late.ngrok-free.dev/models");
QNetworkRequest request(url);
request.setRawHeader("ngrok-skip-browser-warning", "1");

QNetworkReply *reply = manager->get(request);

connect(reply, &QNetworkReply::finished, this, [reply]() {
    QByteArray response = reply->readAll();

    if (reply->error() != QNetworkReply::NoError) {
        qDebug() << "Ошибка запроса:" << reply->errorString();
        reply->deleteLater();
        return;
    }

    qDebug() << "Models JSON:" << response;

    reply->deleteLater();
});
```

### Скачивание выбранной модели

```cpp
QString baseUrl = "https://ninja-primp-late.ngrok-free.dev";
QString modelId = "yolo11n_cls_224e30";
QString downloadUrl = baseUrl + "/models/" + modelId + "/download";

QNetworkAccessManager *manager = new QNetworkAccessManager(this);

QNetworkRequest request(QUrl(downloadUrl));
request.setRawHeader("ngrok-skip-browser-warning", "1");

QNetworkReply *reply = manager->get(request);

connect(reply, &QNetworkReply::finished, this, [reply, modelId]() {
    if (reply->error() != QNetworkReply::NoError) {
        qDebug() << "Ошибка скачивания:" << reply->errorString();
        reply->deleteLater();
        return;
    }

    QByteArray modelBytes = reply->readAll();

    QString fileName = modelId + ".tflite";

    // В реальном приложении путь должен быть директорией данных приложения.
    QFile file(fileName);

    if (!file.open(QIODevice::WriteOnly)) {
        qDebug() << "Не удалось открыть файл для записи";
        reply->deleteLater();
        return;
    }

    file.write(modelBytes);
    file.close();

    qDebug() << "Модель сохранена:" << fileName;

    reply->deleteLater();
});
```

## Рекомендованная логика экрана выбора модели

Для каждой модели:

```text
Если модель не скачана:
    показать кнопку "Скачать"

Если модель скачана:
    показать кнопку "Использовать"

Если модель выбрана:
    показать статус "Активная модель"

Если sha256 на сервере отличается от локального:
    показать "Доступно обновление"
```

## Что важно помнить

1. `localhost` нельзя использовать на телефоне.
2. Для демо используется:

```text
https://ninja-primp-late.ngrok-free.dev
```

3. Для запросов к ngrok обязательно добавлять:

```http
ngrok-skip-browser-warning: 1
```

4. Модель сохраняет клиентское приложение, а не сервер.
5. Сервер только отдаёт файл.
6. Путь сохранения на телефоне выбирает приложение.
7. После скачивания нужно проверять `size_bytes` и `sha256`.
8. TensorFlow Lite должен открывать уже локальный `.tflite` файл.

