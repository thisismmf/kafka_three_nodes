# Kafka Three-Node Cluster with Data Persistence and Monitoring

This project sets up a three-node Kafka cluster using Docker, with the following features:

- Three Kafka brokers for high availability
- Data persistence across restarts using Docker volumes
- AKHQ web UI for Kafka monitoring and management
- Logstash integration for message processing
- Python producer and consumer scripts

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone this repository)
- MacOS (or Linux/Windows with minimal adjustments)

## Quick Start

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/kafka_three_nodes.git
   cd kafka_three_nodes
   ```

2. Start the Kafka cluster and all associated services:
   ```bash
   ./test-setup.sh
   ```

3. Access the AKHQ web UI at http://localhost:8080

## Architecture

The setup includes:

- **ZooKeeper**: For Kafka coordination
- **Kafka Brokers (3)**: Distributed message broker system
- **AKHQ**: Web UI for Kafka monitoring
- **Logstash**: For message processing
- **Python Producer**: Generates sample messages
- **Python Consumer**: Consumes and displays messages

## Data Persistence

All data is persisted in Docker volumes, ensuring:
- Data survives container restarts
- Consistency across the Kafka cluster
- Message retention according to Kafka's retention policies

## Port Mapping

| Service    | Port Mapping        | Purpose                    |
|------------|---------------------|-----------------------------|
| ZooKeeper  | 2181:2181           | ZooKeeper client port       |
| Kafka 1    | 9092:9092           | Kafka broker                |
| Kafka 2    | 9093:9092           | Kafka broker                |
| Kafka 3    | 9094:9092           | Kafka broker                |
| AKHQ       | 8080:8080           | Web UI                      |
| Logstash   | 5044:5044           | Logstash TCP input          |

## Customization

### Creating Additional Topics

To create additional topics, you can:

1. Use AKHQ to create topics through the web UI
2. Use the kafka-topics.sh script directly:

```bash
docker exec kafka1 kafka-topics.sh \
  --bootstrap-server kafka1:9092 \
  --create \
  --topic new-topic \
  --partitions 3 \
  --replication-factor 3
```

## Troubleshooting

1. **Kafka containers not starting**: Check the logs with `docker compose logs kafka1`
2. **Producer/consumer connectivity issues**: Ensure the topic exists with proper partitions and replication
3. **Connection issues**: Make sure all services are healthy with `docker compose ps`

## License

MIT 