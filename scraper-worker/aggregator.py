"""Content Aggregator - Extract metadata and content from any website."""

import requests
from bs4 import BeautifulSoup
import psycopg2
import os
from datetime import datetime
from urllib.parse import urlparse
import json

def extract_images(soup, base_url, limit=3):
    """Extract image URLs from page."""
    images = []
    for img in soup.find_all("img", limit=limit):
        src = img.get("src") or img.get("data-src")
        if src:
            if src.startswith("http"):
                images.append(src)
            elif src.startswith("/"):
                images.append(base_url + src)
    return images[:limit]

def extract_links(soup, base_url, limit=5):
    """Extract external links from page."""
    links = []
    seen = set()
    for link in soup.find_all("a", href=True):
        href = link.get("href", "").strip()
        if href and href.startswith("http") and href not in seen and len(links) < limit:
            seen.add(href)
            text = link.get_text(strip=True)[:100]
            links.append({"url": href, "text": text})
    return links

def extract_key_points(soup, limit=5):
    """Extract key paragraphs/points from content."""
    points = []
    for p in soup.find_all(["p", "h2", "h3"]):
        text = p.get_text(strip=True)
        if len(text) > 20 and len(points) < limit:
            points.append(text[:300])
    return points

def aggregate_content(url):
    """Extract content metadata and structure from any URL."""
    print(f"[📚] Aggregating: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"[❌] Failed to reach {url} - Status: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract title
        title = soup.title.string if soup.title else "Untitled"
        if soup.find("h1"):
            title = soup.find("h1").get_text(strip=True) or title
        title = title[:300]
        
        # Extract description/meta
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "")[:500]
        
        if not description:
            paragraphs = soup.find_all("p")
            if paragraphs:
                description = paragraphs[0].get_text(strip=True)[:500]
        
        # Get domain
        domain = urlparse(url).netloc.replace("www.", "")
        
        # Extract metadata
        base_url = url.rsplit("/", 1)[0]
        images = extract_images(soup, base_url)
        links = extract_links(soup, url)
        key_points = extract_key_points(soup)
        
        # Extract all text for search indexing
        full_text = soup.get_text(separator=" ", strip=True)[:3000]
        
        # Extract keywords from headings and bold text
        keywords = []
        for tag in soup.find_all(["h2", "h3", "strong", "b"]):
            kw = tag.get_text(strip=True)[:50]
            if kw and len(kw) > 3:
                keywords.append(kw)
        keywords = list(set(keywords))[:10]
        
        result = {
            "url": url,
            "title": title,
            "description": description,
            "domain": domain,
            "images": images,
            "links": json.dumps(links),
            "key_points": json.dumps(key_points),
            "full_text": full_text,
            "keywords": json.dumps(keywords),
            "scraped_at": datetime.now().isoformat()
        }
        
        print(f"[✅] Aggregated: {title}")
        return result

    except Exception as e:
        print(f"[❌] Error aggregating {url}: {e}")
        return None


def save_article(data):
    """Save content article to database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "scraper_db"),
            user=os.getenv("POSTGRES_USER", "scraper_user"),
            password=os.getenv("POSTGRES_PASSWORD", "scraper_password")
        )
        cursor = conn.cursor()

        # Create articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                description TEXT,
                domain TEXT,
                thumbnail_image TEXT,
                images TEXT,
                links TEXT,
                key_points TEXT,
                full_text TEXT,
                keywords TEXT,
                saved_at TIMESTAMP DEFAULT NOW(),
                view_count INTEGER DEFAULT 0
            )
        """)

        # Create article_tags table for searching
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_tags (
                id SERIAL PRIMARY KEY,
                article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
                tag TEXT,
                UNIQUE(article_id, tag)
            )
        """)

        # Insert article
        first_image = data["images"][0] if data["images"] else None
        cursor.execute("""
            INSERT INTO articles (url, title, description, domain, thumbnail_image, images, links, key_points, full_text, keywords)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(url) DO UPDATE SET saved_at = NOW(), view_count = articles.view_count + 1
            RETURNING id
        """, (data["url"], data["title"], data["description"], data["domain"], 
              first_image, json.dumps(data["images"]), data["links"], data["key_points"], data["full_text"], data["keywords"]))
        
        article_id = cursor.fetchone()[0]
        
        # Auto-tag based on keywords and domain
        keywords = json.loads(data["keywords"])
        auto_tags = keywords + [data["domain"].split(".")[0]]
        
        for tag in auto_tags[:8]:
            tag = tag.lower()[:50]
            cursor.execute("""
                INSERT INTO article_tags (article_id, tag) VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (article_id, tag))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[📖] Article saved to library with auto-tags!")

    except Exception as e:
        print(f"[❌] Database error: {e}")
