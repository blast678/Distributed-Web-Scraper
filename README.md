# Distributed Web Scraper

This project runs a small Kafka-based scraping pipeline:

- `api-service` accepts URLs and sends them to Kafka.
- `scraper-worker` consumes URLs from Kafka and processes them.
- `kafka`, `zookeeper`, `postgres`, and `jenkins` are started through Docker Compose.

## Run In WSL

These steps were verified in WSL with Docker Compose v2.

### 1. Open WSL and go to the compose folder

```bash
cd /mnt/d/SPIT_sem_6/DEVOPS/Devops_project/Distributed-Web-Scraper/ci-cd
```

### 2. Start the stack

Use `docker compose` rather than the older `docker-compose` binary:

```bash
docker compose up -d --build
```

### 3. Check the services

```bash
docker compose ps
```

Expected services:

- `zookeeper`
- `kafka`
- `postgres`
- `api-service`
- `scraper-worker`
- `jenkins`

### 4. Verify the API

Health check:

```bash
curl -sS http://localhost:8000/health
```

Queue a test URL:

```bash
curl -sS -X POST http://localhost:8000/scrape \
	-H "Content-Type: application/json" \
	-d '{"url":"https://example.com"}'
```

You should get a response like:

```json
{"status":"queued","url":"https://example.com/"}
```

### 5. Check Kafka topics

The API bootstraps the Kafka topic automatically.

```bash
docker compose exec -T kafka kafka-topics --bootstrap-server kafka:29092 --list
```

You should see:

- `urls-to-scrape`

### 6. View logs

```bash
docker compose logs -f api-service
docker compose logs -f scraper-worker
docker compose logs -f kafka
```

### 7. Stop the stack

```bash
docker compose down
```

## Notes

- If you see a warning about `version` in `docker-compose.yml`, it is safe to ignore; Compose v2 simply treats it as obsolete.
- If containers were created with the older `docker-compose` binary and you hit stale-image errors, remove the old project containers and rerun with `docker compose up -d --build`.
- Jenkins runs on `http://localhost:8080`.

## Person 3 Scope

Person 3 owns the API layer:

- `api-service/app.py`
- `api-service/routes/scrape.py`
- `api-service/kafka_producer.py`

The API validates URLs, ensures the Kafka topic exists, and queues requests to Kafka.
