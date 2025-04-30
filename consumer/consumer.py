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
bs = os.getenv("BOOTSTRAP_SERVERS", "kafka1:9093,kafka2:9093,kafka3:9093").split(",")
topic = os.getenv("TOPIC", "my-topic")
group_id = os.getenv("GROUP_ID", "my-consumer-group")
sasl_username = os.getenv("SASL_USERNAME", "client") 
sasl_password = os.getenv("SASL_PASSWORD", "client-secret")

# Check if topic exists
def check_topic_exists(topic_name, bootstrap_servers):
    logger.info(f"Checking if topic {topic_name} exists")
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
            else:
                logger.warning(f"Topic {topic_name} does not exist")
                return False
        except Exception as e:
            attempt += 1
            logger.warning(f"Error checking topic existence: {e}. Retry {attempt}/{max_attempts}")
            time.sleep(5)
    
    logger.error(f"Failed to check if topic exists after {max_attempts} attempts")
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
        # Check if the topic exists first
        if not check_topic_exists(topic, bs):
            logger.warning(f"Topic {topic} does not exist yet. Waiting...")
            attempt += 1
            time.sleep(retry_delay)
            continue
            
        # Create the consumer
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bs,
            group_id=group_id,
            auto_offset_reset='earliest',  # Start from the beginning if no offset is stored
            enable_auto_commit=True,       # Automatically commit offsets
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            security_protocol="SASL_PLAINTEXT",
            sasl_mechanism="SCRAM-SHA-256",
            sasl_plain_username=sasl_username,
            sasl_plain_password=sasl_password
        )
        
        logger.info(f"Connected to Kafka brokers: {bs}")
        logger.info(f"Consuming from topic: {topic} with group: {group_id}")
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