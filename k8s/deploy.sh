#!/bin/bash
set -e

NAMESPACE="payment-processing"
K8S_DIR="$(dirname "$0")"

echo "🚀 Deploying Payment Processing Service to Kubernetes..."
echo ""

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f "$K8S_DIR/namespace.yaml"
kubectl config set-context --current --namespace=$NAMESPACE

# Apply secrets and configmaps
echo "🔐 Applying secrets..."
kubectl apply -f "$K8S_DIR/secret.yaml"
echo "⚙️  Applying configmap..."
kubectl apply -f "$K8S_DIR/configmap.yaml"

# Apply storage
echo "💾 Applying persistent volumes..."
kubectl apply -f "$K8S_DIR/pvc.yaml"

# Apply infrastructure
echo "🐘 Starting PostgreSQL..."
kubectl apply -f "$K8S_DIR/postgres-service.yaml"
kubectl apply -f "$K8S_DIR/postgres-statefulset.yaml"

echo "🔴 Starting Redis..."
kubectl apply -f "$K8S_DIR/redis-statefulset.yaml"

echo "🔧 Starting PgBouncer..."
kubectl apply -f "$K8S_DIR/pgbouncer-configmap.yaml"
kubectl apply -f "$K8S_DIR/pgbouncer-deployment.yaml"
kubectl apply -f "$K8S_DIR/pgbouncer-service.yaml"

echo "🐇 Starting RabbitMQ..."
kubectl apply -f "$K8S_DIR/rabbitmq-statefulset.yaml"

# Wait for infrastructure to be ready
echo "⏳ Waiting for infrastructure to be ready..."
kubectl wait --for=condition=ready pod -l component=postgres --timeout=120s -n $NAMESPACE
kubectl wait --for=condition=ready pod -l component=pgbouncer --timeout=60s -n $NAMESPACE
kubectl wait --for=condition=ready pod -l component=redis --timeout=60s -n $NAMESPACE
kubectl wait --for=condition=ready pod -l component=rabbitmq --timeout=120s -n $NAMESPACE

# Apply application
echo "🔧 Starting backend..."
kubectl apply -f "$K8S_DIR/backend-deployment.yaml"
kubectl apply -f "$K8S_DIR/backend-service.yaml"
kubectl apply -f "$K8S_DIR/backend-hpa.yaml"

echo "👤 Starting consumer..."
kubectl apply -f "$K8S_DIR/consumer-deployment.yaml"

# Apply ingress
echo "🌐 Applying ingress..."
kubectl apply -f "$K8S_DIR/ingress.yaml"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Status:"
kubectl get pods -n $NAMESPACE
echo ""
echo "🔍 Services:"
kubectl get services -n $NAMESPACE
echo ""
echo "🌐 Ingress:"
kubectl get ingress -n $NAMESPACE
echo ""
echo "💡 To view logs:"
echo "  kubectl logs -l app=payment-processing-backend -n $NAMESPACE -f"
echo "  kubectl logs -l app=payment-processing-consumer -n $NAMESPACE -f"
echo ""
echo "💡 To scale backend:"
echo "  kubectl scale deployment payment-processing-backend -n $NAMESPACE --replicas=3"
