# Kubernetes Deployment

## Структура файлов

```
k8s/
├── namespace.yaml                    # Namespace для изоляции
├── secret.yaml                       # Секреты (пароли, ключи)
├── configmap.yaml                    # Конфигурация (переменные окружения)
├── pvc.yaml                          # PersistentVolumeClaims
├── postgres-service.yaml             # Service для PostgreSQL
├── postgres-statefulset.yaml         # StatefulSet для PostgreSQL
├── redis-statefulset.yaml            # StatefulSet для Redis (+ Service)
├── pgbouncer-configmap.yaml          # ConfigMap для PgBouncer (конфиг + userlist)
├── pgbouncer-deployment.yaml         # Deployment для PgBouncer (2 реплики)
├── pgbouncer-service.yaml            # Service для PgBouncer
├── backend-deployment.yaml           # Deployment для backend (+ HPA)
├── backend-service.yaml              # Service для backend
├── backend-hpa.yaml                  # HorizontalPodAutoscaler
├── consumer-deployment.yaml          # Deployment для consumer
├── ingress.yaml                      # Ingress для маршрутизации
├── deploy.sh                         # Скрипт для автоматического деплоя
└── README.md                         # Этот файл
```

## Предварительные требования

- Kubernetes cluster (v1.24+)
- kubectl настроен на cluster
- Container registry с образом `payment-processing-backend-ca:latest`
- StorageClass `standard` (или укажите свой в PVC)
- Ingress controller (nginx)

## Быстрый старт

### 1. Настройка секретов

Отредактируйте `k8s/secret.yaml`:

```yaml
stringData:
  POSTGRES_PASSWORD: "your-secure-password"
  REDIS_PASSWORD: "your-secure-password"
  BACKEND_AUTHENTICATION_HEADER_VALUE: "your-api-key"
```

### 2. Настройка Ingress

Отредактируйте `k8s/ingress.yaml` и укажите ваш домен:

```yaml
tls:
  - hosts:
      - payments.your-domain.com
    secretName: payment-processing-tls
rules:
  - host: payments.your-domain.com
```

### 3. Деплой

```bash
# Автоматический деплой
chmod +x k8s/deploy.sh
./k8s/deploy.sh

# Или поочередно
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/postgres-service.yaml k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-statefulset.yaml
kubectl apply -f k8s/pgbouncer-configmap.yaml k8s/pgbouncer-deployment.yaml k8s/pgbouncer-service.yaml
kubectl apply -f k8s/rabbitmq-statefulset.yaml
kubectl apply -f k8s/backend-deployment.yaml k8s/backend-service.yaml k8s/backend-hpa.yaml
kubectl apply -f k8s/consumer-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

## Управление

### Просмотр статуса

```bash
NAMESPACE="payment-processing"

# Все поды
kubectl get pods -n $NAMESPACE

# Деплойменты
kubectl get deployments -n $NAMESPACE

# Службы
kubectl get services -n $NAMESPACE

# Ingress
kubectl get ingress -n $NAMESPACE

# HPA
kubectl get hpa -n $NAMESPACE
```

### Логи

```bash
NAMESPACE="payment-processing"

# Логи backend
kubectl logs -l app=payment-processing-backend -n $NAMESPACE -f

# Логи consumer
kubectl logs -l app=payment-processing-consumer -n $NAMESPACE -f

# Логи конкретного пода
kubectl logs payment-processing-backend-xxx -n $NAMESPACE -f
```

### Масштабирование

```bash
NAMESPACE="payment-processing"

# Вручную масштабировать backend
kubectl scale deployment payment-processing-backend -n $NAMESPACE --replicas=3

# Включить/отключить HPA
kubectl patch hpa payment-processing-backend-hpa -n $NAMESPACE --type='json' -p='[{"op": "replace", "path": "/spec/minReplicas", "value": 1}]'
```

### Обновление образа

```bash
NAMESPACE="payment-processing"

# Обновить образ backend
kubectl set image deployment/payment-processing-backend \
  backend=payment-processing-backend-ca:v1.2.3 \
  -n $NAMESPACE

# Обновить образ consumer
kubectl set image deployment/payment-processing-consumer \
  consumer=payment-processing-backend-ca:v1.2.3 \
  -n $NAMESPACE

# Проверить статус обновления
kubectl rollout status deployment/payment-processing-backend -n $NAMESPACE
```

### Откат

```bash
NAMESPACE="payment-processing"

# Откатить последнюю версию
kubectl rollout undo deployment/payment-processing-backend -n $NAMESPACE
kubectl rollout undo deployment/payment-processing-consumer -n $NAMESPACE

# История версий
kubectl rollout history deployment/payment-processing-backend -n $NAMESPACE
```

### Удаление

```bash
NAMESPACE="payment-processing"

# Удалить всё
kubectl delete namespace $NAMESPACE

# Или покомпонентно
kubectl delete -f k8s/ --recursive
```

## Ресурсы

### Backend

- **Replicas:** 2 (min), 10 (max)
- **CPU:** 250m-500m
- **Memory:** 256Mi-512Mi
- **Healthcheck:** `/api/v1/healthcheck`
- **Port:** 8000

### Consumer

- **Replicas:** 1
- **CPU:** 250m-500m
- **Memory:** 256Mi-512Mi

### PgBouncer

- **Replicas:** 2
- **Mode:** transaction
- **Max client connections:** 1000
- **Default pool size:** 20
- **Port:** 6432

### PostgreSQL

- **Storage:** 10Gi
- **Type:** StatefulSet (для данных)

### Redis

- **Storage:** 5Gi
- **Type:** StatefulSet (для данных)

### RabbitMQ

- **Storage:** 10Gi
- **Type:** StatefulSet (для данных)

## HPA Configuration

Autoscaling based on:
- **CPU:** 70% average utilization
- **Memory:** 80% average utilization
- **Min replicas:** 2
- **Max replicas:** 10
- **Scale-up:** Stabilization 60s, max 50% or 2 pods per 60s
- **Scale-down:** Stabilization 300s, max 50% per 60s

## Troubleshooting

### Под не стартует

```bash
# Проверить события
kubectl describe pod <pod-name> -n payment-processing

# Проверить логи предыдущего запуска
kubectl logs <pod-name> -n payment-processing --previous

# Проверить конфигурацию
kubectl get pod <pod-name> -n payment-processing -o yaml
```

### Проблемы с базой данных

```bash
# Проверить подключение через PgBouncer
kubectl exec -it <postgres-pod> -n payment-processing -- psql -h pgbouncer-service -p 6432 -U postgres

# Проверить подключение напрямую
kubectl exec -it <postgres-pod> -n payment-processing -- psql -U postgres

# Проверить БД
kubectl exec -it <postgres-pod> -n payment-processing -- psql -U postgres -c "\l"
```

### Проблемы с PgBouncer

```bash
# Проверить подключение к PgBouncer
kubectl run -it --rm debug --image=postgres:17.5 --restart=Never -- \
  psql -h pgbouncer-service -p 6432 -U postgres -d payments

# Проверить пулы PgBouncer
kubectl exec -it <pgbouncer-pod> -n payment-processing -- \
  psql -U postgres -d pgbouncer -c "SELECT * FROM pgbouncer.pools;"

# Проверить количество соединений
kubectl exec -it <pgbouncer-pod> -n payment-processing -- \
  psql -U postgres -d pgbouncer -c "SHOW SERVERS;"
```

### Проблемы с RabbitMQ

```bash
# Проверить очереди
kubectl exec -it <rabbitmq-pod> -n payment-processing -- rabbitmqctl list_queues

# Проверить соединения
kubectl exec -it <rabbitmq-pod> -n payment-processing -- rabbitmqctl list_connections
```

## Monitoring

### Prometheus Metrics

Для мониторинга рекомендуется настроить:
- Prometheus для сбора метрик
- Grafana для визуализации
- Alertmanager для уведомлений

### Jaeger

Для распределенной трассировки:
- Jaeger UI доступен через Service
- Port: 16686

## Security

### Best Practices

1. Используйте secrets management (HashiCorp Vault, AWS Secrets Manager)
2. Включите network policies
3. Настройте RBAC
4. Используйте read-only root filesystem
5. Запускайте поды от non-root user

### Network Policies (опционально)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payment-processing-network-policy
  namespace: payment-processing
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              component: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              component: redis
      ports:
        - protocol: TCP
          port: 6379
    - to:
        - podSelector:
            matchLabels:
              component: rabbitmq
      ports:
        - protocol: TCP
          port: 5672
```
