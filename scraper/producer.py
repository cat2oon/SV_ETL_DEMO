from scraper.product import Product
from confluent_kafka import Producer
from scraper.logger import get_logger


logger = get_logger("kafka")


def when_published(err, msg):
    if not err:
        logger.info(
            f"successfully published: {msg.topic()} [{msg.partition()}] @ {msg.offset()}"
        )
        return

    # TODO: 알람 처리, 마지막 성공/실패 지점 인덱스 기록 (재시도 시 이어서 시작)
    logger.error(f"failed to publish: {err}")


class KafkaProducer:
    def __init__(self, bootstrap_servers: str, client_id: str):
        self.KAFKA_CONFIG = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
        }
        self.producer = Producer(self.KAFKA_CONFIG)

    def publish_event(self, topic: str, key: str, value: bytes):
        self.producer.produce(
            topic=topic, key=key, value=value, callback=when_published
        )
        self.producer.flush()

    def publish_product(self, prod: Product):
        topic = "marketplace.joongonara.product.scraped"  # TODO: hdyra config
        self.publish_event(topic, str(prod.pid), prod.encode_by_avro())
