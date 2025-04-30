import os
import time
import json
import logging
from datetime import datetime
from kafka import KafkaProducer, KafkaAdminClient, errors
from kafka.admin import NewTopic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kafka-producer')

# Get configuration from environment variables
bs = os.getenv("BOOTSTRAP_SERVERS").split(",")
topic = os.getenv("TOPIC")
sasl_username = os.getenv("SASL_USERNAME", "client")
sasl_password = os.getenv("SASL_PASSWORD", "client-secret")

# Try to ensure topic exists
def ensure_topic_exists(bootstrap_servers, topic_name):
    logger.info(f"Ensuring topic {topic_name} exists")
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers,
                security_protocol="SASL_PLAINTEXT",
                sasl_mechanism="SCRAM-SHA-256",
                sasl_plain_username=sasl_username,
                sasl_plain_password=sasl_password
            )
            
            topics = admin_client.list_topics()
            if topic_name in topics:
                logger.info(f"Topic {topic_name} exists")
                return True
            
            logger.info(f"Creating topic {topic_name}")
            topic = NewTopic(
                name=topic_name,
                num_partitions=3,
                replication_factor=3
            )
            admin_client.create_topics([topic])
            logger.info(f"Topic {topic_name} created successfully")
            return True
        except Exception as e:
            attempt += 1
            logger.warning(f"Error ensuring topic exists: {e}. Retry {attempt}/{max_attempts}")
            time.sleep(5)
    
    logger.error(f"Failed to ensure topic exists after {max_attempts} attempts")
    return False

# Create producer with retry logic
max_retries = 10
retry_delay = 5
attempt = 0

# Wait for Kafka to be fully up and running
time.sleep(5)
logger.info("Starting producer setup...")

while attempt < max_retries:
    try:
        # Ensure the topic exists
        if not ensure_topic_exists(bs, topic):
            attempt += 1
            logger.warning(f"Topic verification failed. Retrying in {retry_delay}s (attempt {attempt}/{max_retries})")
            time.sleep(retry_delay)
            continue
            
        producer = KafkaProducer(
            bootstrap_servers=bs,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            security_protocol="SASL_PLAINTEXT",
            sasl_mechanism="SCRAM-SHA-256",
            sasl_plain_username=sasl_username,
            sasl_plain_password=sasl_password
        )
        logger.info(f"Connected to Kafka brokers: {bs}")
        logger.info(f"Producing to topic: {topic}")
        break
    except errors.NoBrokersAvailable:
        attempt += 1
        logger.warning(f"Unable to connect to brokers. Retrying in {retry_delay}s (attempt {attempt}/{max_retries})")
        time.sleep(retry_delay)
    except Exception as e:
        logger.error(f"Failed to create producer: {e}")
        attempt += 1
        time.sleep(retry_delay)

if attempt >= max_retries:
    logger.error("Failed to connect to Kafka after maximum retries")
    exit(1)

# Main production loop
i = 0
while True:
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = {
            "count": i,
            "timestamp": timestamp,
            "message": f"Message #{i}",
        }
        
        future = producer.send(topic, value=msg)
        # Block to get the metadata about the sent message
        record_metadata = future.get(timeout=10)
        
        logger.info(f"Message sent: {msg} | " +
                   f"Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, " +
                   f"Offset: {record_metadata.offset}")
        
        i += 1
        time.sleep(5)
        
    except errors.KafkaError as e:
        logger.error(f"Error sending message: {e}")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        time.sleep(5)  # Wait before retrying