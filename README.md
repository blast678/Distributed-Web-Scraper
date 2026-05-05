# Distributed Web Scraper

A Docker-based distributed web scraping system built with FastAPI, Kafka, PostgreSQL, and a Python worker.

The API accepts URLs, publishes scrape jobs to Kafka, and serves a simple web UI. The worker consumes jobs from Kafka, extracts article metadata/content with BeautifulSoup, and stores the results in PostgreSQL for search, tags, detail views, and analytics.

## Tech Stack

- FastAPI and Uvicorn for the API service
- Apache Kafka and Zookeeper for the scrape queue
- Python worker with Requests and BeautifulSoup4 for scraping
- PostgreSQL for storing scraped articles and generated tags
- Docker Compose for local WSL execution
- Jenkins and Kubernetes manifests for DevOps workflow support

## Project Structure

```text
.
|-- api-service/          # FastAPI app, Kafka producer, routes, static UI
|-- scraper-worker/       # Kafka consumer and scraping/aggregation logic
|-- ci-cd/                # Docker Compose and Jenkins Dockerfile
|-- infrastructure/       # Kubernetes manifests and setup notes
|-- docs/                 # Project report and architecture diagram
|-- Jenkinsfile           # Jenkins pipeline
`-- README.md
```

## Prerequisites

Install or enable these before running:

- WSL 2
- Docker Desktop
- Docker Desktop WSL integration
- Docker Compose v2

Check Docker from WSL:

```bash
docker --version
docker compose version
```

## Run In WSL

### 1. Open WSL

```bash
wsl
```

### 2. Go to the Docker Compose folder

If the project is stored on your Windows `D:` drive, WSL usually exposes it at `/mnt/d`:

```bash
cd /mnt/d/SPIT_sem_6/DEVOPS/Devops_project/Distributed-Web-Scraper/ci-cd
```

If you cloned the project directly inside WSL, use your own project path and then enter `ci-cd`.

### 3. Build and start the stack

Use Docker Compose v2:

```bash
docker compose up -d --build
```

This starts:

- `zookeeper`
- `kafka`
- `postgres`
- `api-service`
- `scraper-worker`
- `jenkins`

### 4. Check running containers

```bash
docker compose ps
```

### 5. Verify the API

```bash
curl -sS http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### 6. Open the web UI

Open this in your Windows browser:

```text
http://localhost:8000
```

Jenkins is available at:

```text
http://localhost:8080
```

## Sample Inputs

Queue a URL for scraping:

```bash
curl -sS -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

More sample URLs:

```bash
curl -sS -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://en.wikipedia.org/wiki/Web_scraping"}'
```

```bash
curl -sS -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://en.wikipedia.org/wiki/Apache_Kafka"}'
```

```bash
curl -sS -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://docs.python.org/3/tutorial/"}'
```

The API should respond with:

```json
{"status":"queued","url":"https://example.com/"}
```

Wait a few seconds for the worker to process the queued URL, then search the stored articles.

## Useful API Endpoints

Health check:

```bash
curl -sS http://localhost:8000/health
```

Get recent articles:

```bash
curl -sS "http://localhost:8000/articles/search"
```

Search articles:

```bash
curl -sS "http://localhost:8000/articles/search?q=python"
```

Get tags:

```bash
curl -sS "http://localhost:8000/articles/tags"
```

Get articles by tag:

```bash
curl -sS "http://localhost:8000/articles/tag/python"
```

Get analytics:

```bash
curl -sS "http://localhost:8000/analytics"
```

Get article details:

```bash
curl -sS "http://localhost:8000/articles/1"
```

## Kafka Checks

The API creates the Kafka topic automatically during startup.

List Kafka topics:

```bash
docker compose exec -T kafka kafka-topics --bootstrap-server kafka:29092 --list
```

Expected topic:

```text
urls-to-scrape
```

## View Logs

API logs:

```bash
docker compose logs -f api-service
```

Worker logs:

```bash
docker compose logs -f scraper-worker
```

Kafka logs:

```bash
docker compose logs -f kafka
```

PostgreSQL logs:

```bash
docker compose logs -f postgres
```

## Stop The Project

Stop containers but keep volumes:

```bash
docker compose down
```

Stop containers and remove volumes, including PostgreSQL and Jenkins data:

```bash
docker compose down -v
```

## Troubleshooting

If `localhost:8000` does not respond, check container status:

```bash
docker compose ps
```

If Kafka or the worker is still starting, watch logs:

```bash
docker compose logs -f kafka scraper-worker api-service
```

If old containers were created with the legacy `docker-compose` command, remove the old stack and rebuild:

```bash
docker compose down
docker compose up -d --build
```

If Docker is unavailable inside WSL, open Docker Desktop and confirm WSL integration is enabled for your distro.

## Notes

- Use `docker compose`, not the older `docker-compose` binary.
- A warning about the `version` field in `docker-compose.yml` is harmless with Compose v2.
- The local API runs on `http://localhost:8000`.
- Jenkins runs on `http://localhost:8080`.
- PostgreSQL data persists in Docker volumes until you run `docker compose down -v`.
