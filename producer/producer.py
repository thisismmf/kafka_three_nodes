import os
import time
import json
import logging
from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import KafkaError, NoBrokersAvailable, TopicAlreadyExistsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kafka-producer')

# Get configuration from environment variables
bs = os.getenv("BOOTSTRAP_SERVERS").split(",")
topic = os.getenv("TOPIC")

# Try to ensure topic exists
def ensure_topic_exists(topic_name, bootstrap_servers):
    logger.info(f"Ensuring topic {topic_name} exists")
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers
        )
        
        existing_topics = admin_client.list_topics()
        if topic_name in existing_topics:
            logger.info(f"Topic {topic_name} already exists")
            return True
            
        logger.info(f"Creating topic {topic_name}")
        topic_config = NewTopic(
            name=topic_name,
            num_partitions=3,
            replication_factor=3
        )
        admin_client.create_topics([topic_config])
        logger.info(f"Topic {topic_name} created successfully")
        return True
    except TopicAlreadyExistsError:
        logger.info(f"Topic {topic_name} already exists")
        return True
    except Exception as e:
        logger.warning(f"Could not create/verify topic: {e}")
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
        # Try to connect to the admin client first
        if not ensure_topic_exists(topic, bs):
            attempt += 1
            logger.warning(f"Topic verification failed. Retrying in {retry_delay}s (attempt {attempt}/{max_retries})")
            time.sleep(retry_delay)
            continue
            
        producer = KafkaProducer(
            bootstrap_servers=bs,
            value_serializer=lambda v: json.dumps(v).encode(),
            acks='all',  # Wait for all replicas to acknowledge
            retries=5,   # Retry sending message if it fails
            retry_backoff_ms=500  # Time between retries
        )
        logger.info(f"Connected to Kafka brokers: {bs}")
        logger.info(f"Producing to topic: {topic}")
        break
    except NoBrokersAvailable:
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
        
    except KafkaError as e:
        logger.error(f"Error sending message: {e}")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        time.sleep(5)  # Wait before retrying