import requests
from bs4 import BeautifulSoup
import json
import psycopg2
import os
from datetime import datetime
import urllib3

# Disable SSL warnings since we are passing through a proxy middleman
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Grab the proxy key injected by Kubernetes
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

def scrape_url(url):
    print(f"[ ] Visiting: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        proxies = None
        
        # Configure the Rotating Proxy
        if SCRAPERAPI_KEY:
            proxy_url = f"http://scraperapi:{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001"
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            print("[ ] Routing traffic through ScraperAPI Rotating Proxy...")

        # IMPORTANT: verify=False is required when using this proxy
        response = requests.get(url, headers=headers, proxies=proxies, verify=False, timeout=20)
        
        if response.status_code != 200:
            print(f"[ ] Failed to reach {url} - Status: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else "No title found"
        paragraphs = soup.find_all("p")
        text_content = " ".join([p.get_text() for p in paragraphs])
        
        result = {
            "url": url,
            "title": title,
            "content": text_content[:2000], # Keep it to 2000 chars for the DB
            "scraped_at": datetime.now().isoformat()
        }
        print(f"[ ] Successfully scraped: {title}")
        return result
        
    except Exception as e:
        print(f"[ ] Error scraping {url}: {e}")
        return None

def save_to_db(data):
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres-service"),
            database=os.getenv("POSTGRES_DB", "scraper_db"),
            user=os.getenv("POSTGRES_USER", "scraper_user"),
            password=os.getenv("POSTGRES_PASSWORD", "scraper_password")
        )
        cursor = conn.cursor()
        
        # Create table if it doesn't exist yet
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraped_results (
                id SERIAL PRIMARY KEY,
                url TEXT,
                title TEXT,
                content TEXT,
                scraped_at TIMESTAMP
            )
        """)
        
        # Insert the scraped data
        cursor.execute("""
            INSERT INTO scraped_results (url, title, content, scraped_at)
            VALUES (%s, %s, %s, %s)
        """, (data["url"], data["title"], data["content"], data["scraped_at"]))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[ ] Data securely saved to PostgreSQL database!")
    except Exception as e:
        print(f"[ ] Database error: {e}")