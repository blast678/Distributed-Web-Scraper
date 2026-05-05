#!/usr/bin/env python3
import requests
import json
import time

API_URL = "http://localhost:8000"

print("=" * 70)
print("CONTENT LIBRARY - LIVE TEST DEMO")
print("=" * 70)

# Test 1: Health Check
print("\n[1️⃣  HEALTH CHECK]")
response = requests.get(f"{API_URL}/health")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Test 2: Submit URLs
print("\n[2️⃣  SUBMIT URLs FOR PROCESSING]")
test_urls = [
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://github.com",
    "https://en.wikipedia.org/wiki/Machine_learning"
]

for url in test_urls:
    try:
        response = requests.post(
            f"{API_URL}/scrape",
            json={"url": url},
            timeout=5
        )
        print(f"✅ {url}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Test 3: Check empty search (shows all articles)
print("\n[3️⃣  SEARCH ALL ARTICLES]")
try:
    response = requests.get(f"{API_URL}/articles/search")
    data = response.json()
    print(f"Total articles: {data.get('count', 0)}")
    if data.get('results'):
        print(f"Results: {len(data['results'])} article(s)")
        for result in data['results'][:3]:
            print(f"  - {result.get('title', 'N/A')} ({result.get('domain', 'N/A')})")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Get all tags
print("\n[4️⃣  GET ALL TAGS]")
try:
    response = requests.get(f"{API_URL}/articles/tags?limit=10")
    data = response.json()
    print(f"Total tags: {data.get('total', 0)}")
    if data.get('tags'):
        print("Top tags:")
        for tag in data['tags'][:5]:
            print(f"  - {tag['name']} ({tag['count']} articles)")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Get analytics
print("\n[5️⃣  GET ANALYTICS]")
try:
    response = requests.get(f"{API_URL}/analytics")
    data = response.json()
    print(f"Total articles collected: {data.get('total_articles', 0)}")
    print(f"Top domains: {len(data.get('top_domains', []))} domain(s)")
    for domain in data.get('top_domains', [])[:3]:
        print(f"  - {domain['domain']}: {domain['count']} articles")
    print(f"Most viewed articles: {len(data.get('most_viewed', []))} article(s)")
    for article in data.get('most_viewed', [])[:2]:
        print(f"  - {article['title']}: {article['views']} views")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETE - Check http://localhost:8000 to see the UI!")
print("=" * 70)
