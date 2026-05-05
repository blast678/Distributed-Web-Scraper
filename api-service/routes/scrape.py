import logging
import os
import time
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, HttpUrl
from kafka_producer import get_producer, send_url_to_kafka
import psycopg2

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

@router.get("/articles/search")
async def search_articles(q: str = "", limit: int = 50):
    """Full-text search articles by query."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "scraper_db"),
            user=os.getenv("POSTGRES_USER", "scraper_user"),
            password=os.getenv("POSTGRES_PASSWORD", "scraper_password")
        )
        cursor = conn.cursor()
        
        if not q:
            # Return recent articles if no search query
            cursor.execute("""
                SELECT id, title, description, domain, full_text, images, view_count, saved_at
                FROM articles
                ORDER BY saved_at DESC
                LIMIT %s
            """, (limit,))
        else:
            # Full-text search
            search_term = f"%{q}%"
            cursor.execute("""
                SELECT id, title, description, domain, full_text, images, view_count, saved_at
                FROM articles
                WHERE title ILIKE %s OR description ILIKE %s OR full_text ILIKE %s
                ORDER BY saved_at DESC
                LIMIT %s
            """, (search_term, search_term, search_term, limit))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "title": row[1],
                "description": row[2][:200] if row[2] else "",
                "domain": row[3],
                "full_text": row[4] if row[4] else "",
                "images": row[5] if row[5] else "[]",
                "view_count": row[6],
                "saved_at": str(row[7]) if row[7] else ""
            })
        
        cursor.close()
        conn.close()
        return {"results": results, "count": len(results), "query": q}
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"results": [], "count": 0, "error": str(e)}

@router.get("/articles/tags")
async def get_tags(limit: int = 100):
    """Get all tags with article counts."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "scraper_db"),
            user=os.getenv("POSTGRES_USER", "scraper_user"),
            password=os.getenv("POSTGRES_PASSWORD", "scraper_password")
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tag, COUNT(*) as count
            FROM article_tags
            GROUP BY tag
            ORDER BY count DESC
            LIMIT %s
        """, (limit,))
        
        rows = cursor.fetchall()
        tags = [{"tag_name": row[0], "article_count": row[1]} for row in rows]
        
        cursor.close()
        conn.close()
        return {"tags": tags, "total": len(tags)}
    
    except Exception as e:
        logger.error(f"Tags error: {e}")
        return {"tags": [], "total": 0}

@router.get("/articles/tag/{tag_name}")
async def articles_by_tag(tag_name: str, limit: int = 50):
    """Get all articles with a specific tag."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "scraper_db"),
            user=os.getenv("POSTGRES_USER", "scraper_user"),
            password=os.getenv("POSTGRES_PASSWORD", "scraper_password")
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.title, a.description, a.domain, a.full_text, a.images, a.view_count, a.saved_at
            FROM articles a
            JOIN article_tags t ON a.id = t.article_id
            WHERE LOWER(t.tag) = LOWER(%s)
            ORDER BY a.saved_at DESC
            LIMIT %s
        """, (tag_name, limit))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "title": row[1],
                "description": row[2][:200] if row[2] else "",
                "domain": row[3],
                "full_text": row[4] if row[4] else "",
                "images": row[5] if row[5] else "[]",
                "view_count": row[6],
                "saved_at": str(row[7]) if row[7] else ""
            })
        
        cursor.close()
        conn.close()
        return {"results": results, "count": len(results), "tag": tag_name}
    
    except Exception as e:
        logger.error(f"Tag filter error: {e}")
        return {"results": [], "count": 0}

@router.get("/analytics")
async def get_analytics():
    """Get library analytics and statistics."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "scraper_db"),
            user=os.getenv("POSTGRES_USER", "scraper_user"),
            password=os.getenv("POSTGRES_PASSWORD", "scraper_password")
        )
        cursor = conn.cursor()
        
        # Total articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        # Top domains
        cursor.execute("""
            SELECT domain, COUNT(*) as count
            FROM articles
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        """)
        top_domains = [{"domain": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Most viewed articles
        cursor.execute("""
            SELECT id, title, view_count, domain
            FROM articles
            ORDER BY view_count DESC
            LIMIT 10
        """)
        most_viewed = [{"id": row[0], "title": row[1], "view_count": row[2], "domain": row[3]} for row in cursor.fetchall()]
        
        # Top tags
        cursor.execute("""
            SELECT tag, COUNT(*) as count
            FROM article_tags
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 10
        """)
        top_tags = [{"tag": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {
            "total_articles": total_articles,
            "top_domains": top_domains,
            "most_viewed": most_viewed,
            "top_tags": top_tags
        }
    
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {"total_articles": 0, "top_domains": [], "most_viewed": [], "top_tags": []}

@router.get("/articles/{article_id}")
async def get_article_detail(article_id: int):
    """Get full article details including all extracted content."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "scraper_db"),
            user=os.getenv("POSTGRES_USER", "scraper_user"),
            password=os.getenv("POSTGRES_PASSWORD", "scraper_password")
        )
        cursor = conn.cursor()
        
        # Get article details
        cursor.execute("""
            SELECT id, url, title, description, domain, full_text, images, links, 
                   key_points, keywords, view_count, saved_at
            FROM articles
            WHERE id = %s
        """, (article_id,))
        
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get associated tags
        cursor.execute("""
            SELECT tag FROM article_tags
            WHERE article_id = %s
            ORDER BY tag
        """, (article_id,))
        
        tags = [row[0] for row in cursor.fetchall()]
        
        # Increment view count
        cursor.execute("""
            UPDATE articles SET view_count = view_count + 1
            WHERE id = %s
        """, (article_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        article_row = row
        return {
            "id": article_row[0],
            "url": article_row[1],
            "title": article_row[2],
            "description": article_row[3],
            "domain": article_row[4],
            "full_text": article_row[5],
            "images": article_row[6],  # Already JSON string
            "links": article_row[7],   # Already JSON string
            "key_points": article_row[8],  # Already JSON string
            "keywords": article_row[9],  # Already JSON string
            "view_count": article_row[10],
            "saved_at": str(article_row[11]) if article_row[11] else "",
            "tags": tags
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

