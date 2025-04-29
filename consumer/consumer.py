import os, json
from kafka import KafkaConsumer

bs = os.getenv("BOOTSTRAP_SERVERS").split(",")
topic = os.getenv("TOPIC")
group = os.getenv("GROUP_ID")
user = os.getenv("SASL_USERNAME")
pwd  = os.getenv("SASL_PASSWORD")

consumer = KafkaConsumer(
    topic,
    bootstrap_servers=bs,
    security_protocol="SASL_PLAINTEXT",
    sasl_mechanism="SCRAM-SHA-256",
    sasl_plain_username=user,
    sasl_plain_password=pwd,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id=group,
    value_deserializer=lambda m: json.loads(m.decode())
)

for record in consumer:
    print("Received:", record.value)