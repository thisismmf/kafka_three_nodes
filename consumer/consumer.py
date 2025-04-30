import os
import json
import logging
import time
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.errors import KafkaError, NoBrokersAvailable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kafka-consumer')

# Get configuration from environment variables
bs = os.getenv("BOOTSTRAP_SERVERS").split(",")
topic = os.getenv("TOPIC")
group = os.getenv("GROUP_ID")

# Check if topic exists
def check_topic_exists(topic_name, bootstrap_servers, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers
            )
            topics = admin_client.list_topics()
            if topic_name in topics:
                logger.info(f"Topic {topic_name} exists")
                return True
            else:
                logger.warning(f"Topic {topic_name} does not exist yet. Attempt {attempt+1}/{max_attempts}")
                time.sleep(5)
        except Exception as e:
            logger.warning(f"Failed to check topic existence: {e}. Attempt {attempt+1}/{max_attempts}")
            time.sleep(5)
    
    logger.warning(f"Topic {topic_name} could not be verified after {max_attempts} attempts")
    return False

# Create consumer with retry logic
max_retries = 10
retry_delay = 5
attempt = 0

# Wait for Kafka to be fully up and running
time.sleep(5)
logger.info("Starting consumer setup...")

# Check if topic exists before creating consumer
if not check_topic_exists(topic, bs):
    logger.warning(f"Topic {topic} may not exist yet, but will try to consume anyway")

while attempt < max_retries:
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bs,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=group,
            value_deserializer=lambda m: json.loads(m.decode()),
            heartbeat_interval_ms=3000,
            session_timeout_ms=30000,
            max_poll_interval_ms=300000
        )
        logger.info(f"Connected to Kafka brokers: {bs}")
        logger.info(f"Consuming from topic: {topic}")
        logger.info(f"Consumer group: {group}")
        break
    except NoBrokersAvailable:
        attempt += 1
        logger.warning(f"Unable to connect to brokers. Retrying in {retry_delay}s (attempt {attempt}/{max_retries})")
        time.sleep(retry_delay)
    except Exception as e:
        logger.error(f"Failed to create consumer: {e}")
        attempt += 1
        time.sleep(retry_delay)

if attempt >= max_retries:
    logger.error("Failed to connect to Kafka after maximum retries")
    exit(1)

# Main consumption loop
try:
    logger.info(f"Started consuming messages from topic {topic}")
    for record in consumer:
        logger.info(f"Received message | " +
                  f"Topic: {record.topic}, Partition: {record.partition}, " +
                  f"Offset: {record.offset}, Key: {record.key}")
        logger.info(f"Message value: {record.value}")
except KafkaError as e:
    logger.error(f"Kafka error during consumption: {e}")
except KeyboardInterrupt:
    logger.info("Consumer stopped by user")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    try:
        consumer.close()
        logger.info("Consumer closed")
    except Exception as e:
        logger.error(f"Error closing consumer: {e}")