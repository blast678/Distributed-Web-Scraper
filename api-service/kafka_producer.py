import json
import logging
from kafka import KafkaAdminClient, KafkaProducer
from kafka.admin import NewTopic
from kafka.errors import KafkaError
from kafka.errors import TopicAlreadyExistsError

logger = logging.getLogger(__name__)

def get_producer(bootstrap_servers: str = "kafka:9092"):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        retries=5,
    )


def ensure_topic_exists(
    bootstrap_servers: str = "kafka:9092",
    topic: str = "urls-to-scrape",
    partitions: int = 1,
    replication_factor: int = 1,
) -> None:
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    try:
        admin_client.create_topics(
            [
                NewTopic(
                    name=topic,
                    num_partitions=partitions,
                    replication_factor=replication_factor,
                )
            ]
        )
        logger.info(f"[+] Kafka topic ensured: {topic}")
    except TopicAlreadyExistsError:
        logger.info(f"[=] Kafka topic already exists: {topic}")
    finally:
        admin_client.close()

def send_url_to_kafka(producer: KafkaProducer, url: str, topic: str = "urls-to-scrape") -> bool:
    try:
        future = producer.send(topic, {"url": url})
        future.get(timeout=10)  # block until confirmed
        logger.info(f"[+] Sent to Kafka: {url}")
        return True
    except KafkaError as e:
        logger.error(f"[-] Kafka send failed: {e}")
        return False
