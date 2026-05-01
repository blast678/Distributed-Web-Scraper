import logging
import os
import time
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, HttpUrl
from kafka_producer import get_producer, send_url_to_kafka

logger = logging.getLogger(__name__)
router = APIRouter()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

class ScrapeRequest(BaseModel):
    url: HttpUrl  # Pydantic validates it's a real URL automatically


def get_or_connect_producer(request: Request):
    producer = request.app.state.producer
    if producer is not None:
        return producer

    for attempt in range(3):
        try:
            producer = get_producer(KAFKA_BOOTSTRAP)
            request.app.state.producer = producer
            logger.info("[+] Kafka producer reconnected")
            return producer
        except Exception as exc:
            logger.warning(f"[-] Kafka reconnect attempt {attempt + 1} failed: {exc}")
            time.sleep(1)

    return None

@router.post("/scrape")
async def scrape(request: Request, body: ScrapeRequest):
    producer = get_or_connect_producer(request)
    if producer is None:
        raise HTTPException(status_code=503, detail="Kafka unavailable")

    success = send_url_to_kafka(producer, str(body.url))

    if not success:
        raise HTTPException(status_code=500, detail="Failed to queue URL")

    logger.info(f"Queued: {body.url}")
    return {"status": "queued", "url": str(body.url)}

@router.get("/health")
async def health():
    return {"status": "ok"}
