import os
import psycopg2
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, HttpUrl

router = APIRouter()
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")


class TrackRequest(BaseModel):
    url: HttpUrl


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres-service"),
        database=os.getenv("POSTGRES_DB", "scraper_db"),
        user=os.getenv("POSTGRES_USER", "scraper_user"),
        password=os.getenv("POSTGRES_PASSWORD", "scraper_password"),
        connect_timeout=5,
    )


@router.post("/track")
async def track_job(request: Request, body: TrackRequest):
    """
    Accepts a job board URL and queues it as a Kafka scraping task.
    Returns immediately — the scraper-worker picks it up asynchronously.
    """
    producer = request.app.state.producer
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka broker unavailable. Check cluster health.")

    from kafka_producer import send_url_to_kafka
    success = send_url_to_kafka(producer, str(body.url))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enqueue URL to Kafka topic.")

    return {"status": "Job Sniper Initiated", "queued_url": str(body.url)}


@router.get("/history")
async def get_job_history(limit: int = 50):
    """
    Returns the latest scraped job listings from the career_jobs table.
    Ordered by most recently scraped. Returns an array of job objects.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure the table exists — safe to run on every call (idempotent)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS career_jobs (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                source TEXT,
                scraped_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()

        cursor.execute("""
            SELECT title, link, source, scraped_at
            FROM career_jobs
            ORDER BY scraped_at DESC
            LIMIT %s;
        """, (limit,))

        records = cursor.fetchall()
        cursor.close()
        conn.close()

        if not records:
            return []

        return [
            {
                "title": r[0],
                "link": r[1],
                "source": r[2],
                "scraped_at": r[3].isoformat() if r[3] else None,
            }
            for r in records
        ]

    except psycopg2.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(request: Request):
    """Simple health probe for Kubernetes liveness checks."""
    kafka_ok = request.app.state.producer is not None
    try:
        conn = get_db_connection()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "operational" if (kafka_ok and db_ok) else "degraded",
        "kafka": "online" if kafka_ok else "offline",
        "database": "online" if db_ok else "offline",
    }
