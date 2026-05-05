from scraper import scrape_url, save_to_db
import os
import json
import time
from kafka import KafkaConsumer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")

print("Starting Scraper Worker...")
print("Attempting to connect to Kafka...")
consumer = None
attempt = 1

# The infinite retry loop to wait for Kafka
while True:
    try:
        consumer = KafkaConsumer(
            'urls-to-scrape',
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='scraper-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print(f"  Worker successfully connected to Kafka at {KAFKA_BROKER} on attempt {attempt}")
        break
    except Exception as e:
        print(f"  Kafka not ready yet. Retrying in 5 seconds... (Attempt {attempt} - {e})")
        time.sleep(5)
        attempt += 1

print("  Listening for URLs on queue 'urls-to-scrape'...")
try:
    for message in consumer:
        data = message.value
        url = data.get('url')
        print(f"\n[+] Picked up task from queue: {url}")
        
        result = scrape_url(url)
        if result:
            save_to_db(result)
            print("[ ] Scrape complete and saved to database! Ready for next task.")
        else:
            print("[ ] Scraping failed. Moving to next task.")
except Exception as e:
    print(f"Worker crashed during scraping: {e}")