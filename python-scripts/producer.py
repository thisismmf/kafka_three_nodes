from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
    security_protocol='PLAINTEXT',
    sasl_mechanism='PLAIN',
    sasl_plain_username='python',
    sasl_plain_password='python-secret',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',
    retries=5,
)
for i in range(10):
    data = {'number': i}
    producer.send(topic='my-topic', value=data)
    print(f"Sent: {data}")
producer.flush()
producer.close()
