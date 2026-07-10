#!/bin/bash
######################################
# Declare RabbitMQ exchanges an queues
######################################
RABBITMQ_USERNAME=$(grep -m 1 RABBITMQ_USERNAME .env| cut -d'=' -f2)
RABBITMQ_PASSWORD=$(grep -m 1 RABBITMQ_PASSWORD .env| cut -d'=' -f2)
CONSUMER_EXCHANGE_NAME=$(grep -m 1 CONSUMER_EXCHANGE_NAME .env| cut -d'=' -f2)
CONSUMER_PAYMENT_ROUTING_KEY=$(grep -m 1 CONSUMER_PAYMENT_ROUTING_KEY .env| cut -d'=' -f2)
CONSUMER_QUEUE_NAME=$(grep -m 1 CONSUMER_QUEUE_NAME .env| cut -d'=' -f2)
CONSUMER_QUEUE_DELIVERY_LIMIT=$(grep -m 1 CONSUMER_QUEUE_DELIVERY_LIMIT .env| cut -d'=' -f2)
CONSUMER_DLX_EXCHANGE_NAME=$(grep -m 1 CONSUMER_DLX_EXCHANGE_NAME .env| cut -d'=' -f2)
CONSUMER_DEAD_LETTER_ROUTING_KEY=$(grep -m 1 CONSUMER_DEAD_LETTER_ROUTING_KEY .env| cut -d'=' -f2)
CONSUMER_DLQ_QUEUE_NAME=$(grep -m 1 CONSUMER_DLQ_QUEUE_NAME .env| cut -d'=' -f2)
CONSUMER_DLQ_QUEUE_MESSAGE_TTL=$(grep -m 1 CONSUMER_DLQ_QUEUE_MESSAGE_TTL .env| cut -d'=' -f2)

echo "RABBITMQ_USERNAME=$RABBITMQ_USERNAME"
echo "RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD"
echo "CONSUMER_EXCHANGE_NAME=$CONSUMER_EXCHANGE_NAME"
echo "CONSUMER_PAYMENT_ROUTING_KEY=$CONSUMER_PAYMENT_ROUTING_KEY"
echo "CONSUMER_QUEUE_NAME=$CONSUMER_QUEUE_NAME"
echo "CONSUMER_QUEUE_DELIVERY_LIMIT=$CONSUMER_QUEUE_DELIVERY_LIMIT"
echo "CONSUMER_DLX_EXCHANGE_NAME=$CONSUMER_DLX_EXCHANGE_NAME"
echo "CONSUMER_DEAD_LETTER_ROUTING_KEY=$CONSUMER_DEAD_LETTER_ROUTING_KEY"
echo "CONSUMER_DLQ_QUEUE_NAME=$CONSUMER_DLQ_QUEUE_NAME"
echo "CONSUMER_DLQ_QUEUE_MESSAGE_TTL=$CONSUMER_DLQ_QUEUE_MESSAGE_TTL"

CONSUMER_QUEUE_ARGUMENTS="{\"x-queue-type\":\"quorum\",\"x-overflow\":\"reject-publish\",\"x-dead-letter-exchange\":\"$CONSUMER_DLX_EXCHANGE_NAME\",\"x-dead-letter-routing-key\":\"$CONSUMER_DEAD_LETTER_ROUTING_KEY\",\"x-delivery-limit\":$CONSUMER_QUEUE_DELIVERY_LIMIT,\"x-dead-letter-strategy\":\"at-least-once\"}"
echo "CONSUMER_QUEUE_ARGUMENTS=$CONSUMER_QUEUE_ARGUMENTS"

CONSUMER_DLQ_QUEUE_ARGUMENTS="{\"x-queue-type\":\"quorum\",\"x-message-ttl\":$CONSUMER_DLQ_QUEUE_MESSAGE_TTL}"
echo "CONSUMER_DLQ_QUEUE_ARGUMENTS=$CONSUMER_DLQ_QUEUE_ARGUMENTS"

docker compose exec -T rabbitmq rabbitmqadmin -u $RABBITMQ_USERNAME -p $RABBITMQ_PASSWORD declare exchange name=$CONSUMER_EXCHANGE_NAME type=topic durable=true
docker compose exec -T rabbitmq rabbitmqadmin -u $RABBITMQ_USERNAME -p $RABBITMQ_PASSWORD declare queue name=$CONSUMER_QUEUE_NAME durable=true arguments=$CONSUMER_QUEUE_ARGUMENTS
docker compose exec -T rabbitmq rabbitmqadmin -u $RABBITMQ_USERNAME -p $RABBITMQ_PASSWORD declare exchange name=$CONSUMER_DLX_EXCHANGE_NAME type=fanout durable=true
docker compose exec -T rabbitmq rabbitmqadmin -u $RABBITMQ_USERNAME -p $RABBITMQ_PASSWORD declare queue name=$CONSUMER_DLQ_QUEUE_NAME durable=true arguments=$CONSUMER_DLQ_QUEUE_ARGUMENTS
docker compose exec -T rabbitmq rabbitmqadmin -u $RABBITMQ_USERNAME -p $RABBITMQ_PASSWORD declare binding source=$CONSUMER_EXCHANGE_NAME destination=$CONSUMER_QUEUE_NAME routing_key=$CONSUMER_PAYMENT_ROUTING_KEY
docker compose exec -T rabbitmq rabbitmqadmin -u $RABBITMQ_USERNAME -p $RABBITMQ_PASSWORD declare binding source=$CONSUMER_DLX_EXCHANGE_NAME destination=$CONSUMER_DLQ_QUEUE_NAME routing_key=$CONSUMER_DEAD_LETTER_ROUTING_KEY
