import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routes.scrape import router as scrape_router
from kafka_producer import ensure_topic_exists, get_producer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect Kafka producer
    try:
        ensure_topic_exists(KAFKA_BOOTSTRAP)
        app.state.producer = get_producer(KAFKA_BOOTSTRAP)
        logger.info("[+] Kafka producer connected")
    except Exception as e:
        logger.warning(f"[-] Kafka not available at startup: {e}")
        app.state.producer = None
    yield
    # Shutdown: flush & close
    if app.state.producer:
        app.state.producer.flush()
        app.state.producer.close()
        logger.info("[+] Kafka producer closed")

app = FastAPI(title="Distributed Web Scraper API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limiting globally via middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

app.include_router(scrape_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
