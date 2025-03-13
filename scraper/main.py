import trio
import hydra
import random

from omegaconf import DictConfig
from scraper.decorators import wrap_log
from scraper.logger import get_logger
from scraper.fetcher import fetch_page
from scraper.product import (
    Product,
    extract_product,
    extract_recent_prod_ids,
)
from scraper.producer import KafkaProductProducer

logger = get_logger("main")


def fetch_pids_to_visit(
    url_recent: str, num_visits: int, randomize: bool = False
) -> list[str]:
    html = fetch_page(url_recent)
    if not html:
        return []

    recent_pids = extract_recent_prod_ids(html)
    most_recent_id = recent_pids[0]
    search_start_id = int(most_recent_id) - num_visits
    pids = [str(i) for i in range(search_start_id, int(most_recent_id) + 1)]

    if randomize:
        random.shuffle(pids)
    return pids


@wrap_log("fetch: {prod_id}")
async def fetch_product(url: str, prod_id: str) -> Product:
    html = fetch_page(url)
    if not html:
        logger.error(f"fetch 실패: {url}")
        return Product.from_error(prod_id, "FETCH FAILED")
    return extract_product(html, prod_id)


def gen_prod_fetcher(prod_base_url: str):
    async def worker(rec_channel_pid, send_channel_kafka):
        try:
            async for pid in rec_channel_pid:
                target_url = prod_base_url.format(pid=pid)
                prod = await fetch_product(target_url, pid)
                await send_channel_kafka.send(prod)
        except trio.ClosedResourceError:
            # TODO: send_channel_pid 종료 시 kafka 채널 대기하도록 수정
            # EOF 메시지 혹은 done 시그널
            pass
        except Exception as e:
            logger.error(f"exception occur: {e}")
        finally:
            await send_channel_kafka.aclose()

    return worker


def gen_kafka_producer(kafka_cfg: DictConfig):
    producer = KafkaProductProducer(kafka_cfg.bootstrap_servers, kafka_cfg.client_id)

    # TODO: 배치로 묶어서 카프카 전송
    async def kafka_producer(channel):
        async with channel:
            async for prod in channel:
                logger.info(f"publish product: {prod.pid}")
                producer.publish_product(prod)
                # await trio.sleep(2)  # for timing test

    return kafka_producer


async def async_main(cfg: DictConfig) -> None:
    num_visits = cfg.scraper.num_visits
    url_recent = cfg.urls.recent
    use_random = cfg.scraper.random_visit

    # 방문할 상품 아이디 범위 생성
    pids = fetch_pids_to_visit(url_recent, num_visits, use_random)

    if len(pids) == 0:
        logger.error("최신 상품 페이지 조회 실패로 종료")
        return

    # 작업자 간 메모리 채널 생성
    send_channel_pid, rec_channel_pid = trio.open_memory_channel(0)
    send_channel_kafka, rec_channel_kafka = trio.open_memory_channel(0)

    # 작업자 생성
    product_fetcher = gen_prod_fetcher(cfg.urls.product)
    kafka_producer = gen_kafka_producer(cfg.kafka)

    # 작업자 실행
    num_workers = cfg.scraper.num_workers
    async with trio.open_nursery() as nursery:
        nursery.start_soon(kafka_producer, rec_channel_kafka)
        for _ in range(num_workers):
            nursery.start_soon(product_fetcher, rec_channel_pid, send_channel_kafka)

        # 비동기 카프카_저장(상품_스크랩(상품_아이디))
        async with send_channel_pid:
            for pid in pids:
                await send_channel_pid.send(pid)

    logger.info(">>> scrap task is complete <<<")


@hydra.main(version_base=None, config_path="", config_name="config")
def main(cfg: DictConfig) -> None:
    trio.run(async_main, cfg)


if __name__ == "__main__":
    main()
