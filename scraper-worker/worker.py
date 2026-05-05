from aggregator import aggregate_content, save_article
import os
import json
import time
from kafka import KafkaConsumer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")

print("🚀 Starting Content Aggregator Worker...")
print("Attempting to connect to Kafka...")

consumer = None
attempt = 1

while True:
    try:
        consumer = KafkaConsumer(
            'urls-to-scrape',
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='aggregator-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print(f"✅ Worker connected to Kafka at {KAFKA_BROKER} on attempt {attempt}")
        break
    except Exception as e:
        print(f"⏳ Kafka not ready. Retrying in 5 seconds... (Attempt {attempt})")
        time.sleep(5)
        attempt += 1

print("📚 Listening for URLs on 'urls-to-scrape' queue...")

try:
    for message in consumer:
        data = message.value
        url = data.get('url')
        print(f"\n[📥] Processing: {url}")

        result = aggregate_content(url)

        if result:
            save_article(result)
            print("[✅] Content saved to library! Ready for next task.")
        else:
            print("[❌] Aggregation failed. Moving to next task.")

except Exception as e:
    print(f"Worker error: {e}")