import os, time, json
from kafka import KafkaProducer

bs = os.getenv("BOOTSTRAP_SERVERS").split(",")
topic = os.getenv("TOPIC")
user = os.getenv("SASL_USERNAME")
pwd  = os.getenv("SASL_PASSWORD")

producer = KafkaProducer(
    bootstrap_servers=bs,
    security_protocol="SASL_PLAINTEXT",
    sasl_mechanism="SCRAM-SHA-256",
    sasl_plain_username=user,
    sasl_plain_password=pwd,
    value_serializer=lambda v: json.dumps(v).encode()
)

i = 0
while True:
    msg = {"count": i}
    producer.send(topic, value=msg)
    print("Sent:", msg)
    producer.flush()
    i += 1
    time.sleep(5)