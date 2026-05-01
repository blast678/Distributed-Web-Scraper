import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)
router = APIRouter()

class ScrapeRequest(BaseModel):
    url: HttpUrl  # Pydantic validates it's a real URL automatically

@router.post("/scrape")
async def scrape(request: Request, body: ScrapeRequest):
    producer = request.app.state.producer
    if producer is None:
        raise HTTPException(status_code=503, detail="Kafka unavailable")

    from kafka_producer import send_url_to_kafka
    success = send_url_to_kafka(producer, str(body.url))

    if not success:
        raise HTTPException(status_code=500, detail="Failed to queue URL")

    logger.info(f"Queued: {body.url}")
    return {"status": "queued", "url": str(body.url)}

@router.get("/health")
async def health():
    return {"status": "ok"}
