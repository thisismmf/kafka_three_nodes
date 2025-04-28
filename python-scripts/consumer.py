from kafka import KafkaProducer
import json

consumer = KafkaConsumer(
    'test',
    bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
    security_protocol='PLAINTEXT',
    sasl_mechanism='PLAIN',
    sasl_plain_username='python',
    sasl_plain_password='python-secret',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='1',
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
)
print("Waiting for messages...")
for message in consumer:
    print(f"topic: {message.topic}, partition: {message.partition}, offset: {message.offset}, key: {message.key}, value: {message.value}")