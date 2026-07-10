# Асинхронный сервис процессинга платежей (Clean Architecture)

## Описание
___
Микросервис для асинхронной обработки платежей (Clean Architecture):
- принимает запросы на оплату;
- обрабатывает их через внешний платежный шлюз (эмуляцию);
- уведомляет клиента о результате через webhook.

## Компоненты
___

### API (FastAPI, FastStream-Outbox)
___
Сервис REST API для обработки запросов:
- `POST /api/v1/payments` - Создание нового платежа:
  - `Idempotency key` для защиты от дублей
  - статический API ключ в заголовке `X-API-Key`
- `GET /api/v1/payments/{payment_id}` - Получение данных указанного платежа:
  - статический API ключ в заголовке `X-API-Key`
- `POST /api/v1/webhooks` - Обработка webhook уведомления
  - эмулирует обработку webhook уведомления (90% успех, 10% ошибка)
- `GET /api/v1/healthcheck` - Проверка работоспособности сервиса

### Comsumer (FastStream)
___
Сервис обработки сообщений в очереди RabbitMQ:
- получает сообщение из очереди `payments.new`
- эмулирует обработку платежа (2-5 сек, 90% успех, 10% ошибка)
- обновляет статус в БД
- отправляет webhook уведомление на указанный URL (выполняет 3 попытки отправки вебхука)
- реализует повторную отправку сообщения в очередь `payments.new` в случае ошибки обработки события
- реализует отправку события после 3 попыток обработки в DLQ очередь `payments.new.dlq` 


### Установка
___
Процесс установки описан для операционной системы Linux и предполагает использование следующих каталогов:
- `/opt/test-payment-processing-service-ca` - каталог с исходным кодом проекта
- `/opt/test-payment-processing-service-ca-data` - каталог для хранения данных проекта (PostgreSQL, Redis, RabbitMQ)

В файле `.env.sample` значение каталога для хранения данных указано в переменной `PROJECT_DATA_DIR=/opt/test-payment-processing-service-ca-data`. 
Для изменения каталога для хранения данных необходимо изменить значение переменной `PROJECT_DATA_DIR`.
Значения остальные переменных с каталогами указаны относительно значения переменной `PROJECT_DATA_DIR`.

#### Шаги установки:
- создать каталоги для хранения данных
```shell
cd /opt
sudo mkdir -p /opt/test-payment-processing-service-ca-data/{backups,db,rabbitmq,redis,redis-insight}
sudo chown -R {user}:{group} test-payment-processing-service-ca-data
```
- клонировать проект
```shell
cd /opt
sudo git clone https://github.com/serker72/test-payment-processing-service-ca.git
sudo chown -R {user}:{group} test-payment-processing-service-ca
```
- скопировать файл `.env.sample` с именем `.env`
```shell
cd /opt/test-payment-processing-service-ca
cp .env.sample .env
```
- при необходимости, внести изменения в файл `.env`
- выполнить сборку образа контейнеров
```shell
cd /opt/test-payment-processing-service-ca
docker compose build
```
- применить миграции БД, убедиться в отсутствии ошибок
```shell
cd /opt/test-payment-processing-service-ca
docker compose -f docker-compose.db-update.yml up -d && docker logs -f payment-processing-ca-db-update
docker compose -f docker-compose.db-update.yml down
```
- запустить сервис
```shell
cd /opt/test-payment-processing-service-ca
docker compose up -d
docker ps
```

#### Проверка работоспособности сервиса
___
План проверки:
- выполнить запрос `POST /api/v1/payments` для создания платежа
- скопировать значение поля `payment_id` из результата выполнения запроса
- выполнить запрос `GET /api/v1/payments/{payment_id}` для получения данных созданного платежа
- проверить значение статуса в поле `status` в результате выполнения запроса - должен отличаться от `pending`
- если значение статуса равно `pending` - повторно выполнить запрос `GET /api/v1/payments/{payment_id}`

##### Postman
Для проверки работоспособности сервиса можно использовать `Postman`, в каталоге проекта есть файл с коллекцией запросов `local-test-tasks.postman_collection.json`.

Для запроса `POST /api/v1/payments` реализован механизм автоматической генерации значения заголовка `Idempotency-Key`.


##### Curl
При использовании `curl` генерировать значения заголовка `Idempotency-Key` нужно будет самостоятельно:
```shell
api_key=$(grep -m 1 BACKEND_AUTHENTICATION_HEADER_KEY .env| cut -d'=' -f2) && \
api_key_value=$(grep -m 1 BACKEND_AUTHENTICATION_HEADER_VALUE .env| cut -d'=' -f2) && \
idempotency_key=$(uuidgen) && \
curl --location --request POST 'http://localhost:8000/api/v1/payments' \
--header 'Content-Type: application/json' \
--header "Idempotency-Key: $idempotency_key" \
--header "$api_key: $api_key_value" \
--data-raw '{
  "amount": 1001,
  "currency": "RUB",
  "description": "Test #2026-06-26",
  "meta_data": {
    "address": "TRx0000000000000001",
    "fio": "Testov Testovik",
    "exp_date": "12/30",
    "bank": "Test Bank",
    "phone": "+79281000001"
  },
  "webhook_url": "https://test.example.com/webhooks/payments"
}'
```
