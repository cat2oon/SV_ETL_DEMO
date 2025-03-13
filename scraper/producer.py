from scraper.product import Product
from scraper.logger import get_logger
from confluent_kafka.avro import AvroProducer


logger = get_logger("kafka")


def when_published(err, msg):
    if not err:
        logger.info(
            f"successfully published: {msg.topic()} [{msg.partition()}] @ {msg.offset()}"
        )
        return

    # TODO: 알람 처리, 마지막 성공/실패 지점 인덱스 기록 (재시도 시 이어서 시작)
    logger.error(f"failed to publish: {err}")


class KafkaProductProducer:
    def __init__(self, bootstrap_servers: str, client_id: str):
        key_schema, value_schema = Product.get_schema_in_key_value()

        self.KAFKA_CONFIG = {
            "schema.registry.url": "http://localhost:8081",
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
        }

        logger.info(f"create kafka producer by config: {self.KAFKA_CONFIG}")
        self.producer = AvroProducer(
            self.KAFKA_CONFIG,
            default_key_schema=key_schema,
            default_value_schema=value_schema,
        )

    def publish_event(self, topic: str, key: int, value: bytes):
        self.producer.produce(
            topic=topic, key=key, value=value, callback=when_published
        )
        self.producer.flush()

    def publish_product(self, prod: Product):
        topic = "marketplace.joongonara.product.scraped"  # TODO: hdyra config
        self.publish_event(topic, prod.pid, prod.to_dict())
