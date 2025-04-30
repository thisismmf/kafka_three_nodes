#!/usr/bin/env bash
set -euo pipefail

KAFKA_BIN=/opt/bitnami/kafka/bin
BROKER=${KAFKA_BOOTSTRAP_SERVERS:-kafka1:9093}
CLIENT_CONFIG="/opt/bitnami/kafka/config/client.properties"

# Create JAAS config for client auth
cat > /tmp/kafka_jaas.conf <<EOF
KafkaClient {
  org.apache.kafka.common.security.scram.ScramLoginModule required
    username="admin"
    password="adminpwd";
};
EOF
export KAFKA_OPTS="-Djava.security.auth.login.config=/tmp/kafka_jaas.conf"

echo "⏱ Waiting for broker metadata on $BROKER…"
i=0
until $KAFKA_BIN/kafka-topics.sh \
        --bootstrap-server "$BROKER" \
        --command-config "$CLIENT_CONFIG" \
        --list \
      >/dev/null 2>&1
do
  ((i++))
  echo "   still waiting… ($i)"
  sleep 2
  if [ $i -gt 30 ]; then
    echo "⚠️  Giving up after $i tries."
    exit 1
  fi
done

echo "✅ Broker is up — creating topic and ACLs…"

# Create topic with 3 partitions and replication factor of 3
$KAFKA_BIN/kafka-topics.sh \
  --bootstrap-server "$BROKER" \
  --command-config "$CLIENT_CONFIG" \
  --create \
  --if-not-exists \
  --topic my-topic \
  --partitions 3 \
  --replication-factor 3

echo "✅ Topic created. Adding ACLs..."

# Add ACLs for the client user to read, write and describe the topic
$KAFKA_BIN/kafka-acls.sh \
  --bootstrap-server "$BROKER" \
  --command-config "$CLIENT_CONFIG" \
  --add \
  --allow-principal User:client \
  --operation Read \
  --operation Write \
  --operation Describe \
  --topic my-topic

echo "✅ Topic ACLs added. Setting up consumer group ACLs..."

# Add consumer group ACLs
$KAFKA_BIN/kafka-acls.sh \
  --bootstrap-server "$BROKER" \
  --command-config "$CLIENT_CONFIG" \
  --add \
  --allow-principal User:client \
  --operation Read \
  --group my-group

# Add cluster-level ACLs for logstash consumer group
$KAFKA_BIN/kafka-acls.sh \
  --bootstrap-server "$BROKER" \
  --command-config "$CLIENT_CONFIG" \
  --add \
  --allow-principal User:client \
  --operation Read \
  --group logstash-group

echo "✅ All setup completed successfully!"
echo "✅ Topic 'my-topic' created and ACLs applied"