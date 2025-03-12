import io
import fastavro

from scraper.product import Product
from scraper.logger import get_logger
from confluent_kafka import OFFSET_STORED

from bytewax import operators as op
from bytewax.dataflow import Dataflow
from bytewax._bytewax import run_main
from bytewax.operators import StatefulBatchLogic
from bytewax.connectors.kafka import operators as kop
from bytewax.connectors.kafka import KafkaSink as KSink
from bytewax.connectors.kafka import KafkaSinkMessage as KSinkMsg

# bytewax 파이썬 패키지는 3.13에서 최근 버전을 제공하지 않아 3.11.11 버전 사용
# 참고: https://docs.bytewax.io/stable/api/bytewax/bytewax.operators.html

logger = get_logger("streams.filter")


def decode_product(message):
    key, value = message.key, message.value
    # bytewax가 이후 파이프라인에서 '키' 타입을 문자열로 요구
    key = str(int(key.decode()))  # byte(alpha_numeric) -> 문자열
    product = Product.decode_by_avro(value)
    return key, product


def filter_price(message):
    key, value = message
    if value["price"] > 1000000:  # 100만원 이상 버리기
        logger.info(f"price filtered key: {key}")
        return False
    return True


# TODO: KEY 기반 카테고리별 합계 계산
class SumLogic(StatefulBatchLogic):
    def __init__(self):
        self.sum = 0

    def on_batch(self, batch):
        for event in batch:
            key, value = event
            self.sum += value["price"]
            logger.info(f"key: {key}, price: {value['price']}, sum: {self.sum}")
        return [(key, self.sum)], False

    def snapshot(self):
        return self.sum

    def restore(self, snapshot):
        self.sum = snapshot


def to_ksink_msg(message):
    _, key_to_price = message
    _, accum_price = key_to_price
    bytes_writer = io.BytesIO()
    schema = fastavro.parse_schema(
        {
            "name": "product_filtered_by_outlier_price",
            "type": "record",
            "fields": [
                {"name": "accum_price", "type": "string"},
            ],
        }
    )
    fastavro.schemaless_writer(bytes_writer, schema, {"accum_price": str(accum_price)})
    return KSinkMsg(None, bytes_writer.getvalue())


def build_data_flow(brokers, source_topic, target_topic, batch_size, kafka_cfg):
    flow = Dataflow("product-filter-streams")

    kin = kop.input(
        "product-in",
        flow,
        brokers=brokers,
        starting_offset=OFFSET_STORED,
        batch_size=batch_size,
        topics=[source_topic],
        add_config=kafka_cfg,
    )

    op.inspect("inspect_err", kin.errs).then(op.raises, "raise_errors")

    # processing
    decoded = op.map("decode_product", kin.oks, decode_product)
    filtered = op.filter("filter_price", decoded, filter_price)

    # TODO: 분산 스트림 앱에 대한
    key_on = op.key_on("batch_grouping", filtered, lambda _: "unique-each-batch")
    # op.inspect("mapping_items", key_on)
    summed = op.stateful_batch("accum_price_batch", key_on, lambda _: SumLogic())
    # summed = op.stateful_map("sum_prices", keyed, aggregate_price)

    to_sink_msg = op.map("to_sink_msg", summed, to_ksink_msg)

    op.output(
        "product-filtered-sum-out",
        to_sink_msg,
        KSink(brokers, target_topic),
    )

    return flow


if __name__ == "__main__":
    logger.info("start kafka streams filter")

    # TODO: hydra 설정으로 정보 일원화 + 데이터 클래스
    batch_size = 10
    source_topic = "marketplace.joongonara.product.scraped"
    target_topic = "marketplace.joongonara.product.filtered.sum"
    brokers = ["172.18.0.8:19092,172.18.0.7:39092,172.18.0.6:29092"]
    kafka_cfg = {
        "group.id": "group.kstreams.filtered.sum",
        "enable.auto.commit": "true",
    }

    # 아래 문서에 따르면 일반적인 컨슈머와 다르게 컨슈머 그룹으로 오프셋 저장하지 않는 듯
    # 저장된 OFFSET_STORTED를 사용해야 마지막 오프셋에 이어 읽을 수 있음
    # https://docs.bytewax.io/stable/guide/concepts/kafka.html#kafka-and-recovery

    run_main(
        build_data_flow(brokers, source_topic, target_topic, batch_size, kafka_cfg)
    )

    logger.info("finish kafka streams filter")
