# Тестирование Payment Processing Service

## Установка зависимостей

```bash
# Установка всех зависимостей через uv
uv sync

# Установка только dev-зависимостей
uv pip install -e ".[dev]"
```

## Запуск тестов локально

### 1. Unit-тесты (без внешних сервисов)

```bash
# Запуск всех тестов
uv run pytest tests/ -v

# С покрытием
uv run pytest tests/ -v --cov=src/payment_processing_service --cov-report=term-missing

# Только определённый слой
uv run pytest tests/domain/ -v
uv run pytest tests/application/ -v
uv run pytest tests/infrastructure/ -v
uv run pytest tests/presentation/ -v
```

### 2. Интеграционные тесты (PostgreSQL + Redis + RabbitMQ + Kafka в Docker)

```bash
# Запуск всех интеграционных тестов
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/ -v

# Запуск конкретных типов тестов
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/ -v -m "api"
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/ -v -m "integration"

# Только Kafka-тесты
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/test_integration.py::TestKafkaIntegration -v

# Только RabbitMQ-тесты
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/test_integration.py::TestRabbitMQIntegration -v

# Запуск конкретного файла
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/test_api_dishka.py -v
```

## Запуск тестов в Docker

### 1. Запуск контейнера test-runner

```bash
# Запуск всех сервисов (PostgreSQL, Redis, RabbitMQ, Kafka, Jaeger, Backend, Consumer)
docker compose -f docker-compose.test.yml up -d

# Запуск контейнера для тестов (остается запущенным)
docker compose -f docker-compose.test.yml up -d test-runner

# Проверка статуса
docker compose -f docker-compose.test.yml ps test-runner
```

### 2. Запуск тестов

```bash
# Все тесты
docker compose -f docker-compose.test.yml exec test-runner pytest tests/ -v

# С покрытием
docker compose -f docker-compose.test.yml exec test-runner pytest tests/ -v --cov=src/payment_processing_service --cov-report=term-missing
```

### 3. Запуск отдельных тестов

```bash
# Только API-тесты (тестируют API-слой с мокированной инфраструктурой)
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/ -v -m "api"

# Только тесты с внешними сервисами (PostgreSQL, RabbitMQ, Kafka)
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/ -v -m "integration"

# Только Kafka-тесты
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/ -v -k "kafka"

# Только unit-тесты
docker compose -f docker-compose.test.yml exec test-runner pytest tests/domain/ tests/application/ -v

# Все интеграционные тесты
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/ -v

# Только определённый файл
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/test_api_dishka.py -v
```

## Структура тестов

```
tests/
├── conftest.py                          # Глобальные фикстуры (mock-объекты, константы)
├── domain/
│   ├── value_objects/                   # Value objects (Currency, PaymentStatus)
│   └── entities/                        # Domain entities (PaymentEntity)
├── application/
│   ├── mappers/                         # Application mappers (Entity <-> DTO)
│   └── use_cases/                       # Use cases (Create, Process, Execute, etc.)
├── infrastructure/
│   ├── db/                              # DB layer (Repositories, UoW, Mappers)
│   ├── mappers/                         # Infrastructure mappers (DTO <-> JSON)
│   ├── http/                            # HTTP clients (WebhookClient)
│   └── broker/                          # Message broker (RabbitPublisher)
├── presentation/
│   ├── schemas/                         # Pydantic схемы (Requests, Responses)
│   ├── mappers/                         # Presentation mappers (DTO <-> API)
│   └── helpers/                         # Helpers (CustomJSON, etc.)
└── integration/
    ├── test_api_dishka.py               # Интеграционные тесты API (моки инфраструктуры) [маркер: api]
    └── test_integration.py              # Интеграционные тесты с PostgreSQL + RabbitMQ + Kafka [маркер: integration]
```

## Маркеры тестов

```bash
# Только API-тесты (тестируют API-слой с мокированной инфраструктурой)
pytest tests/integration/ -v -m "api"

# Только тесты с внешними сервисами (PostgreSQL, RabbitMQ, Kafka)
pytest tests/integration/ -v -m "integration"

# Только Kafka-тесты
pytest tests/ -v -k "kafka"

# Все тесты
pytest tests/ -v
```

## Интеграционные тесты с Kafka

Kafka-тесты находятся в `tests/integration/test_integration.py` в классе `TestKafkaIntegration`:

- `test_kafka_connection` — проверка подключения к Kafka, публикация и чтение сообщения
- `test_kafka_dlq_ttl_config` — проверка конфигурации DLQ-темы (TTL = 7 дней / 604800000 мс)
- `test_kafka_publish_and_consume` — публикация JSON-сообщения и чтение через consumer

Для запуска:

```bash
docker compose -f docker-compose.test.yml exec test-runner pytest tests/integration/test_integration.py::TestKafkaIntegration -v
```

## Фикстуры

### AllureTestClient

Наследник `fastapi.testclient.TestClient` с поддержкой Allure steps:
- Переопределяет методы `get` и `post` с `@allure.step`
- Автоматически добавляет шаги в Allure-отчёт для каждого HTTP-запроса

### Dishka Mock Provider (для тестирования API)

Используется для изоляции API слоя от инфраструктуры без мокирования repository:

- `test_app` - создаёт FastAPI приложение с middleware и роутерами
- `test_app_with_mock_container` - AllureTestClient с мокированным Dishka контейнером
- `test_app_with_container` - AllureTestClient с production контейнером (реальная БД, Redis, RabbitMQ)
- `mock_get_payment_use_case` - мокированный use case для получения платежа
- `mock_create_payment_use_case` - мокированный use case для создания платежа
- `mock_process_webhook_use_case` - мокированный use case для обработки вебхука
- `mock_async_redis_backend` - мокированный Redis backend для idempotency

### Mock-объекты

- `MockRepository` - Mock репозитория
- `MockUnitOfWork` - Mock Unit of Work
- `MockMessageBroker` - Mock брокера сообщений
- `MockWebhookClient` - Mock HTTP-клиента

### Фабрики данных (polyfactory + faker)

- `PaymentEntityFactory` - Фабрика для PaymentEntity
- `PaymentDTOPartialFactory` - Фабрика для PaymentDTO
- `PaymentCreateNotificationDTOPartialFactory` - Фабрика для NotificationDTO

## Генерация отчётов

### Запуск с Allure отчётами

Allure-отчёты содержат:
- `@allure.title` — названия тестов
- `@allure.step` — шаги HTTP-запросов (GET/POST) через AllureTestClient

```bash
# Запуск сервисов allure и allure-ui
docker compose -f docker-compose.test.yml up -d allure allure-ui

# Запуск тестов с генерацией Allure отчётов
docker compose -f docker-compose.test.yml exec test-runner pytest tests/ -v --alluredir=/app/allure-results

# Сервис allure автоматически обнаруживает новые результаты и генерирует отчет

# Просмотр отчета в браузере
# http://localhost:5252
```

### Покрытие кода

```bash
# Запуск с покрытием кода
docker compose -f docker-compose.test.yml exec test-runner pytest tests/ -v --cov=src/payment_processing_service --cov-report=term-missing
```

## Зависимости для тестирования

- `pytest` - Фреймворк для тестов
- `pytest-asyncio` - Поддержка async/await
- `pytest-cov` - Покрытие кода
- `pytest-postgresql` - PostgreSQL для тестов
- `pytest-rabbitmq` - RabbitMQ для тестов
- `pytest-timeout` - Таймауты для тестов
- `pytest-dependency` - Зависимости между тестами
- `faker` - Генерация тестовых данных
- `polyfactory` - Фабрики данных
- `allure-pytest` - Allure отчёты

## CI/CD

Для интеграции с CI/CD можно использовать:

```yaml
# Пример для GitHub Actions
- name: Run tests
  run: |
    docker compose -f docker-compose.test.yml up -d
    docker compose -f docker-compose.test.yml exec test-runner pytest tests/ -v --cov=src/payment_processing_service --cov-report=term-missing
    docker compose -f docker-compose.test.yml down
```
