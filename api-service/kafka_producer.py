import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

def get_producer(bootstrap_servers: str = "kafka:9092"):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        retries=5,
    )

def send_url_to_kafka(producer: KafkaProducer, url: str, topic: str = "urls-to-scrape") -> bool:
    try:
        future = producer.send(topic, {"url": url})
        future.get(timeout=10)  # block until confirmed
        logger.info(f"[+] Sent to Kafka: {url}")
        return True
    except KafkaError as e:
        logger.error(f"[-] Kafka send failed: {e}")
        return False
