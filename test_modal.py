#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Test URLs
test_urls = [
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://github.com",
    "https://en.wikipedia.org/wiki/Machine_learning"
]

print("=" * 70)
print("🚀 TESTING DETAIL VIEW MODAL & TECH STACK")
print("=" * 70)

# Submit URLs
print("\n📤 Submitting URLs for processing...")
for url in test_urls:
    try:
        response = requests.post(f"{BASE_URL}/scrape", json={"url": url})
        if response.status_code == 200:
            print(f"  ✅ {url}")
        else:
            print(f"  ❌ {url}: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

# Wait for processing
print("\n⏳ Waiting 12 seconds for Kafka worker to process...")
time.sleep(12)

# Get articles
print("\n📚 Fetching articles from database...")
try:
    response = requests.get(f"{BASE_URL}/articles/search")
    data = response.json()
    
    if data["results"]:
        print(f"  ✅ Found {len(data['results'])} articles\n")
        
        # Test detail endpoint
        print("🔍 Testing detail view modal endpoint...")
        for i, article in enumerate(data["results"][:1], 1):
            article_id = article["id"]
            print(f"\n  📄 Article #{i}: {article['title']}")
            print(f"     Domain: {article['domain']}")
            print(f"     Views: {article['view_count']}")
            
            # Get full detail
            detail_response = requests.get(f"{BASE_URL}/articles/{article_id}")
            if detail_response.status_code == 200:
                detail = detail_response.json()
                print(f"\n  ✅ Detail View Data Retrieved:")
                print(f"     - URL: {detail['url']}")
                print(f"     - Title: {detail['title']}")
                print(f"     - Domain: {detail['domain']}")
                print(f"     - Description: {detail['description'][:100]}...")
                
                # Parse JSON fields
                if detail.get("images"):
                    images = json.loads(detail["images"])
                    print(f"     - Images: {len(images)} found")
                    if images:
                        print(f"       First image: {images[0][:60]}...")
                
                if detail.get("links"):
                    links = json.loads(detail["links"])
                    print(f"     - Links: {len(links)} found")
                
                if detail.get("key_points"):
                    key_points = json.loads(detail["key_points"])
                    print(f"     - Key Points: {len(key_points)} found")
                
                if detail.get("keywords"):
                    keywords = json.loads(detail["keywords"])
                    print(f"     - Keywords: {len(keywords)} found")
                    print(f"       {', '.join(keywords[:5])}")
                
                if detail.get("tags"):
                    print(f"     - Auto-generated Tags: {len(detail['tags'])} found")
                    print(f"       {', '.join(detail['tags'][:5])}")
                
                print(f"\n  📱 Modal will display:")
                print(f"     🎨 Tech Stack: Apache Kafka, PostgreSQL, FastAPI, BeautifulSoup4, Python, Docker, Kubernetes, HTML5/CSS3, JavaScript, Uvicorn, Zookeeper, psycopg2")
                print(f"     🖼️  Images Gallery: {len(json.loads(detail.get('images', '[]')))} images")
                print(f"     🔗 External Links: {len(json.loads(detail.get('links', '[]')))} links")
                print(f"     🏷️  Keywords Cloud: {len(json.loads(detail.get('keywords', '[]')))} keywords")
                print(f"     📌 Auto-tags: {', '.join(detail.get('tags', [])[:5])}")
            else:
                print(f"  ❌ Failed to get detail: {detail_response.status_code}")
        
        # Test tags
        print("\n\n🏷️  Testing tags endpoint...")
        tags_response = requests.get(f"{BASE_URL}/articles/tags")
        if tags_response.status_code == 200:
            tags_data = tags_response.json()
            print(f"  ✅ {len(tags_data['tags'])} unique tags found")
            print(f"     Top tags: {', '.join([t['tag_name'] for t in tags_data['tags'][:5]])}")
        
        # Test analytics
        print("\n\n📊 Testing analytics endpoint...")
        analytics_response = requests.get(f"{BASE_URL}/analytics")
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            print(f"  ✅ Total articles: {analytics['total_articles']}")
            print(f"     Top domains: {', '.join([d['domain'] for d in analytics['top_domains'][:3]])}")
            print(f"     Most viewed: {analytics['most_viewed'][0]['title'] if analytics['most_viewed'] else 'N/A'}")
        
    else:
        print(f"  ❌ No articles found")
        
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ DETAIL VIEW MODAL SYSTEM READY FOR TESTING")
print("=" * 70)
print("\n📲 Open http://localhost:8000 in your browser and click on any article card!")
print("   The modal will show:")
print("   - Full article content with extracted text")
print("   - Image gallery from the website")
print("   - External links found")
print("   - Auto-generated keywords")
print("   - Auto-detected tags")
print("   - 🚀 TECHNOLOGY STACK VISUALIZATION: All 12 technologies used!")
