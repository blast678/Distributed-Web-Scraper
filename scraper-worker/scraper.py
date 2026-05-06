"""
Career-Sniper Scraper Worker — Multi-Source Job Aggregator
Supports:
  - Hacker News Jobs (Static HTML)
  - WeWorkRemotely Tech/Programming (RSS/XML)
  - RemoteOK Dev Jobs (RSS/XML)
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _fetch(url: str) -> requests.Response | None:
    """Fetch a URL with optional ScraperAPI proxy. Returns the response or None."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; CareerSniperBot/2.0; "
            "+https://github.com/career-sniper)"
        )
    }
    proxies = None
    if SCRAPERAPI_KEY:
        proxy_url = f"http://scraperapi:{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001"
        proxies = {"http": proxy_url, "https": proxy_url}

    try:
        response = requests.get(
            url, headers=headers, proxies=proxies,
            verify=False, timeout=20
        )
        if response.status_code != 200:
            print(f"[-] HTTP {response.status_code} for {url}")
            return None
        return response
    except requests.RequestException as e:
        print(f"[-] Network error fetching {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Parser: Hacker News Jobs (Static HTML)
# ---------------------------------------------------------------------------

def _parse_hacker_news(response: requests.Response) -> list[dict]:
    """Parse HN /jobs page — extracts job listings from table rows."""
    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []

    rows = soup.find_all("tr", class_="athing")
    for row in rows:
        titleline = row.find("span", class_="titleline")
        if not titleline:
            continue
        link_tag = titleline.find("a")
        if not link_tag:
            continue

        title = link_tag.text.strip()
        link = link_tag.get("href", "")

        # Fix relative HN links (e.g., item?id=12345)
        if link.startswith("item?id="):
            link = f"https://news.ycombinator.com/{link}"

        if title and link:
            jobs.append({
                "title": title,
                "link": link,
                "source": "Hacker News",
                "scraped_at": datetime.utcnow().isoformat(),
            })

    return jobs


# ---------------------------------------------------------------------------
# Parser: Generic RSS / Atom feed (WeWorkRemotely, RemoteOK, etc.)
# ---------------------------------------------------------------------------

def _parse_rss_feed(response: requests.Response, source_name: str) -> list[dict]:
    """
    Parse RSS/XML job feeds. Handles both standard RSS <item> elements
    and Atom <entry> elements. Falls back gracefully on malformed XML.
    """
    jobs = []
    try:
        # Strip BOM / encoding declaration issues
        content = response.content
        root = ET.fromstring(content)
    except ET.ParseError:
        # Try lxml-style fallback via BeautifulSoup XML parser
        try:
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item") or soup.find_all("entry")
            for item in items:
                title_tag = item.find("title")
                link_tag = item.find("link")
                title = title_tag.get_text(strip=True) if title_tag else None
                link = (
                    link_tag.get("href")
                    or link_tag.get_text(strip=True)
                    if link_tag else None
                )
                if title and link:
                    # Clean RSS entity encoding
                    title = title.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                    jobs.append({
                        "title": title,
                        "link": link,
                        "source": source_name,
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
            return jobs
        except Exception as e:
            print(f"[-] XML parse fallback also failed for {source_name}: {e}")
            return []

    # Walk all namespaces — handle both RSS and Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item") or root.findall(".//atom:entry", ns)

    for item in items:
        # Title — try both RSS and Atom
        title_el = item.find("title")
        if title_el is None:
            title_el = item.find("atom:title", ns)
        title = (title_el.text or "").strip() if title_el is not None else None

        # Link — RSS uses <link> text, Atom uses <link href="..."/>
        link_el = item.find("link")
        if link_el is None:
            link_el = item.find("atom:link", ns)
            
        if link_el is not None:
            link = link_el.get("href") or (link_el.text or "").strip()
        else:
            link = None

        # RemoteOK puts the real URL in <guid>
        if not link or link.startswith("https://remoteok.com/l/"):
            guid_el = item.find("guid")
            if guid_el is not None and guid_el.text:
                candidate = guid_el.text.strip()
                if candidate.startswith("http"):
                    link = candidate

        # Skip entries with no usable title or link
        if not title or not link:
            continue

        # Strip CDATA / HTML tags from title if present
        if "<" in title:
            title = BeautifulSoup(title, "html.parser").get_text(strip=True)

        # Remove WeWorkRemotely category prefix like "[Full-Stack Programming] "
        if "]" in title:
            title = title.split("]", 1)[-1].strip()

        jobs.append({
            "title": title,
            "link": link,
            "source": source_name,
            "scraped_at": datetime.utcnow().isoformat(),
        })

    return jobs


# ---------------------------------------------------------------------------
# Source router
# ---------------------------------------------------------------------------

SOURCE_MAP = {
    "ycombinator": ("Hacker News", _parse_hacker_news),
    "weworkremotely": ("WeWorkRemotely", _parse_rss_feed),
    "remoteok": ("RemoteOK", _parse_rss_feed),
}


def scrape_url(url: str) -> list[dict] | None:
    """
    Main entry-point called by the Kafka worker.
    Routes to the correct parser based on domain pattern in the URL.
    """
    print(f"[~] Initiating scrape for: {url}")

    response = _fetch(url)
    if response is None:
        return None

    # Identify source
    source_name = "Unknown"
    parser_fn = None

    for domain_key, (name, fn) in SOURCE_MAP.items():
        if domain_key in url:
            source_name = name
            parser_fn = fn
            break

    if parser_fn is None:
        # Generic RSS fallback for unknown feeds
        print(f"[?] Unknown source, attempting generic RSS parse: {url}")
        parser_fn = _parse_rss_feed
        source_name = url.split("/")[2]  # use hostname as source name

    # RSS parsers need the source name injected; HTML parser doesn't
    if parser_fn == _parse_rss_feed:
        jobs = parser_fn(response, source_name)
    else:
        jobs = parser_fn(response)

    print(f"[+] Extracted {len(jobs)} jobs from {source_name} ({url})")
    return jobs


# ---------------------------------------------------------------------------
# Database persistence
# ---------------------------------------------------------------------------

def save_to_db(jobs: list[dict]) -> None:
    """
    Persist a list of job dicts to the career_jobs PostgreSQL table.
    Uses ON CONFLICT DO NOTHING to deduplicate by unique link.
    """
    if not jobs:
        print("[-] No jobs to save.")
        return

    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres-service"),
            database=os.getenv("POSTGRES_DB", "scraper_db"),
            user=os.getenv("POSTGRES_USER", "scraper_user"),
            password=os.getenv("POSTGRES_PASSWORD", "scraper_password"),
        )
        cursor = conn.cursor()

        # Idempotent schema creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS career_jobs (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                source TEXT,
                scraped_at TIMESTAMP DEFAULT NOW()
            )
        """)

        inserted = 0
        for job in jobs:
            cursor.execute("""
                INSERT INTO career_jobs (title, link, source, scraped_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (link) DO NOTHING
                RETURNING id;
            """, (
                job["title"],
                job["link"],
                job["source"],
                job["scraped_at"],
            ))
            if cursor.fetchone():
                inserted += 1

        conn.commit()
        cursor.close()
        conn.close()
        skipped = len(jobs) - inserted
        print(
            f"[+] PostgreSQL Vault: {inserted} NEW jobs stored, "
            f"{skipped} duplicates skipped."
        )

    except Exception as e:
        print(f"[-] Database error: {e}")