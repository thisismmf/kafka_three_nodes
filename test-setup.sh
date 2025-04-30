#!/bin/bash
set -e

echo "🚀 Starting Kafka cluster and services..."
docker compose down --volumes
docker compose up -d

echo "⏱ Waiting for services to be ready (30 seconds)..."
sleep 30

echo "📋 Check service status:"
docker compose ps

echo "📊 Check Kafka broker status:"
docker logs kafka1 | tail -n 20

echo "📊 Create topic if needed:"
docker exec -i kafka1 bash -c 'kafka-topics.sh \
  --bootstrap-server kafka1:9092 \
  --create \
  --if-not-exists \
  --topic my-topic \
  --partitions 3 \
  --replication-factor 3'

echo "📊 Check topic details:"
docker exec -i kafka1 bash -c 'kafka-topics.sh \
  --bootstrap-server kafka1:9092 \
  --describe \
  --topic my-topic'

echo "📝 Check producer logs:"
docker logs kafka-producer | tail -n 10

echo "📝 Check consumer logs:"
docker logs kafka-consumer | tail -n 10

echo "✅ Setup test completed!"
echo
echo "🔶 Access AKHQ at: http://localhost:8080"
echo
echo "🔶 To stop all services run: docker compose down" 