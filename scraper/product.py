import io
import re
import json
import avro.io
import avro.schema

from datetime import datetime
from bs4 import BeautifulSoup
from confluent_kafka import avro as kavro
from scraper.logger import get_logger
from dataclasses import asdict, dataclass

logger = get_logger("PROD")


key_schema = kavro.load("scraper/schema/producer/product/KeySchema.avsc")
value_schema = kavro.load("scraper/schema/producer/product/ValueSchema.avsc")


@dataclass
class Product:
    pid: int
    price: int
    title: str
    description: str
    condition: str
    category_path: str = ""
    error_cause: str = ""
    scraped_at: str = ""

    def __post_init__(self):
        self.scraped_at = datetime.now().isoformat()

    @staticmethod
    def get_schema_in_key_value():
        return key_schema, value_schema

    def from_error(pid: str, error_cause: str) -> "Product":
        return Product(
            pid=int(pid),
            price="",
            title="",
            description="",
            condition="",
            category_path="",
            error_cause=error_cause,
        )

    @staticmethod
    def from_prod_json(pid: str, prod_json: dict, category_json: dict) -> "Product":
        title = prod_json.get("name")
        desc = prod_json.get("description")
        offer = prod_json.get("offers", {})[0]
        price = offer.get("price")
        condition = parse_condition(offer.get("itemCondition"))

        category_path = ""
        if category_json:
            category_elems = category_json.get("itemListElement", [])
            category_path = ">".join(e.get("item").get("name") for e in category_elems)

        return Product(
            pid=int(pid),
            price=price,
            title=title,
            description=desc,
            condition=condition,
            category_path=category_path,
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def decode_avro_value(byte_data: io.BytesIO) -> "Product":
        bytes_reader = io.BytesIO(byte_data[5:])
        decoder = avro.io.BinaryDecoder(bytes_reader)
        datum_reader = avro.io.DatumReader(value_schema)
        return datum_reader.read(decoder)

    @staticmethod
    def decode_avro_key(byte_data: io.BytesIO) -> int:
        bytes_reader = io.BytesIO(byte_data[5:])
        decoder = avro.io.BinaryDecoder(bytes_reader)
        datum_reader = avro.io.DatumReader(key_schema)
        return datum_reader.read(decoder)


def parse_condition(cond: str) -> str:
    if cond == "https://schema.org/UsedCondition":
        return "used"
    elif cond == "https://schema.org/NewCondition":
        return "new"
    return "unknown"


def extract_product(html: str, prod_id: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")
    if not soup:
        logger.error(f"html 파싱 오류: {prod_id}")
        return None

    # TODO: 게시자 삭제 등으로 데이터 없어진 케이스 처리 할 것

    prod_json, category_json = None, None
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    for script in scripts:
        try:
            js = json.loads(script.string)
            type = js.get("@type")
            if prod_json and category_json:
                break
            elif type == "Product":
                prod_json = js
            elif type == "BreadcrumbList":
                category_json = js
        except json.JSONDecodeError:
            continue

    if not prod_json:
        logger.warning(f"상품 정보 없음: {prod_id}")
        return Product.from_error(prod_id, "NO PRODUCT INFO")

    if prod_json.get("sku") != prod_id:
        logger.warning(f"상품 정보 오류: {prod_id}")
        return Product.from_error(prod_id, "INVALID PRODUCT ID")

    return Product.from_prod_json(prod_id, prod_json, category_json)


def extract_recent_prod_ids(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    regex = re.compile(r"^/product/\d+$")
    prod_links = soup.find_all("a", href=regex)

    if not prod_links:
        logger.error(f"상품 정보 없음")
        return []

    return [a.get("href").split("/")[-1] for a in prod_links]
