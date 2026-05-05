# Distributed Content Library

## Full Project Overview

Distributed Content Library is a content collection, organization, and discovery platform. It allows users to submit useful web pages, automatically extracts meaningful information from them, and stores the processed content in a searchable library.

The project is not only a web scraper. Web scraping is the ingestion mechanism. The real purpose of the system is to build a personal or team content library where collected articles, documentation pages, references, blogs, and resources can be searched, tagged, viewed, and analyzed later.

Instead of manually saving links without context, this system turns each submitted URL into a structured content record. It extracts the page title, description, domain, images, links, key points, full text, keywords, tags, saved time, and view count. This makes saved web content easier to revisit, filter, understand, and reuse.

The platform uses a distributed architecture so that user interaction remains fast while heavier content extraction work happens in the background. The API quickly accepts the URL and queues it. A worker service later processes the URL and stores the enriched result in PostgreSQL.

## What The Project Is About

The project is about transforming scattered web links into an organized knowledge library.

Many users save useful links in browser bookmarks, notes, chats, or documents. Over time, those links become difficult to search and understand because they only store the URL, not the actual content or context. This project solves that by extracting and storing useful metadata and readable content from each page.

The system behaves like a lightweight content management and knowledge discovery tool:

- Users submit URLs.
- The system collects page content.
- Extracted data is stored in a database.
- Articles can be searched by title, description, domain, or full text.
- Tags are generated from extracted keywords and domains.
- Users can open detailed views of saved content.
- Analytics show content trends such as top domains, top tags, and most viewed articles.

## Problem Statement

People often discover useful web resources but lose track of them later. Browser bookmarks and plain URL lists are limited because they do not store searchable article text, tags, summaries, images, or metadata. As the number of saved links grows, finding the right resource becomes harder.

At the same time, extracting content from websites can be slow. If scraping is performed directly inside the user request, the application can become unresponsive. Some websites take time to load, network requests may fail, and parsing can require additional processing.

This project solves both problems:

- It creates a structured content library instead of a simple link list.
- It performs content extraction asynchronously using Kafka and a worker service.
- It stores processed results in PostgreSQL for search, browsing, and analytics.
- It keeps the user-facing API responsive while background workers handle heavier tasks.

## What The Project Solves

Distributed Content Library solves these key problems:

- Scattered links are converted into organized content records.
- Saved pages become searchable by text, title, domain, and tags.
- Users can view extracted content without manually reopening every page.
- The API remains fast because scraping runs in the background.
- Kafka prevents submitted URLs from being lost during processing.
- PostgreSQL provides persistent storage for articles and metadata.
- The system can be scaled by adding more worker services.
- Docker Compose makes the full stack easy to run locally in WSL.

## Core Idea

The core idea is simple:

```text
Submit URL -> Extract Content -> Store In Library -> Search And Analyze Later
```

The value of the project is not just downloading webpages. The value is creating a reusable, searchable, and structured library from online content.

## System Architecture

```text
User / Browser
    |
    v
Content Library UI
    |
    v
FastAPI Backend
    |
    v
Kafka Queue
    |
    v
Content Aggregator Worker
    |
    v
PostgreSQL Content Library
    |
    v
Search, Tags, Detail Views, Analytics
```

## End-To-End Flow

1. The user opens the content library web UI.
2. The user submits a URL that they want to save.
3. The FastAPI backend validates the URL.
4. The API sends the URL to Kafka as a background job.
5. Kafka stores the job in the `urls-to-scrape` topic.
6. The worker service consumes the URL from Kafka.
7. The worker downloads the webpage.
8. BeautifulSoup parses the HTML.
9. The aggregator extracts useful content and metadata.
10. PostgreSQL stores the processed article.
11. Tags are generated from keywords and domain data.
12. The user can search, browse, open, and analyze saved content from the UI.

## Content Extraction Flow

For each submitted URL, the worker attempts to collect:

- Page URL
- Page title
- Page description
- Website domain
- Thumbnail image
- Additional image URLs
- External links
- Key points from paragraphs and headings
- Full text for search
- Keywords from headings and emphasized text
- Auto-generated tags
- Saved timestamp
- View count

This turns a raw link into a richer content item.

## Main Features

### 1. URL Submission

Users can submit URLs from the web UI or through the API. The system validates the URL before queueing it.

Endpoint:

```text
POST /scrape
```

### 2. Asynchronous Processing

The submitted URL is not processed directly inside the API request. It is sent to Kafka first. This keeps the API responsive and allows scraping to happen in the background.

### 3. Content Library Storage

Processed content is stored in PostgreSQL. This gives the application persistent article records that remain available even after containers restart, as long as Docker volumes are preserved.

### 4. Search

Users can search saved content by query. The search endpoint checks title, description, and full text.

Endpoint:

```text
GET /articles/search?q=python
```

### 5. Tags

The system creates tags from extracted keywords and page domains. Tags help group related articles and improve browsing.

Endpoints:

```text
GET /articles/tags
GET /articles/tag/{tag_name}
```

### 6. Article Detail View

The UI includes a detail modal where users can inspect a saved article with extracted content, images, links, keywords, and tags.

Endpoint:

```text
GET /articles/{article_id}
```

### 7. Analytics

The analytics endpoint gives a summary of the content library.

It shows:

- Total articles
- Top domains
- Most viewed articles
- Top tags

Endpoint:

```text
GET /analytics
```

### 8. Web Interface

The project includes a browser-based UI served by FastAPI. It allows users to interact with the content library without needing to run curl commands.

UI:

```text
http://localhost:8000
```

## Main Components

### API Service

Location:

```text
api-service/
```

The API service is the user-facing backend. It receives URL submissions, serves the UI, communicates with Kafka, and exposes article/search/tag/analytics routes.

Important files:

- `app.py`: FastAPI application setup.
- `routes/scrape.py`: Routes for URL submission, search, tags, analytics, and article details.
- `kafka_producer.py`: Kafka producer and topic creation logic.
- `static/index.html`: Content library frontend.
- `requirements.txt`: API dependencies.
- `Dockerfile`: API container configuration.

### Kafka And Zookeeper

Kafka acts as the queue between the API and the worker. It makes the system asynchronous and more reliable under load.

Kafka topic:

```text
urls-to-scrape
```

Zookeeper supports the local Kafka setup used in Docker Compose.

### Content Aggregator Worker

Location:

```text
scraper-worker/
```

The worker is responsible for turning URLs into structured library items. It consumes Kafka messages, downloads webpages, extracts content, and saves records to PostgreSQL.

Important files:

- `worker.py`: Kafka consumer loop.
- `aggregator.py`: Main content extraction and database save logic.
- `scraper.py`: Simpler scraping helper.
- `requirements.txt`: Worker dependencies.
- `Dockerfile`: Worker container configuration.

### PostgreSQL Database

PostgreSQL stores the content library.

Main tables:

- `articles`: Stores article metadata, extracted text, images, links, keywords, and view count.
- `article_tags`: Stores generated tags linked to articles.

### Docker Compose

Location:

```text
ci-cd/docker-compose.yml
```

Docker Compose runs the local development stack:

- Zookeeper
- Kafka
- PostgreSQL
- API service
- Scraper worker
- Jenkins

### Jenkins And Kubernetes

The project also includes DevOps assets:

- `Jenkinsfile`
- `ci-cd/Dockerfile.jenkins`
- `infrastructure/k8s/`

These files show how the project can move from local Docker Compose execution toward automated CI/CD and Kubernetes-style deployment.

## API Endpoints

```text
GET  /health
POST /scrape
GET  /articles/search
GET  /articles/tags
GET  /articles/tag/{tag_name}
GET  /articles/{article_id}
GET  /analytics
```

## Example Usage

Submit a URL:

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://en.wikipedia.org/wiki/Web_scraping"}'
```

Expected response:

```json
{
  "status": "queued",
  "url": "https://en.wikipedia.org/wiki/Web_scraping"
}
```

Search the library:

```bash
curl "http://localhost:8000/articles/search?q=web"
```

View tags:

```bash
curl "http://localhost:8000/articles/tags"
```

View analytics:

```bash
curl "http://localhost:8000/analytics"
```

## How To Run In WSL

Open WSL:

```bash
wsl
```

Go to the Docker Compose folder:

```bash
cd /mnt/d/SPIT_sem_6/DEVOPS/Devops_project/Distributed-Web-Scraper/ci-cd
```

Build and start the stack:

```bash
docker compose up -d --build
```

Check services:

```bash
docker compose ps
```

Open the content library UI:

```text
http://localhost:8000
```

Check API health:

```bash
curl http://localhost:8000/health
```

Watch worker logs:

```bash
docker compose logs -f scraper-worker
```

Stop the project:

```bash
docker compose down
```

Remove containers and volumes:

```bash
docker compose down -v
```

## Sample URLs

```text
https://example.com
https://en.wikipedia.org/wiki/Web_scraping
https://en.wikipedia.org/wiki/Apache_Kafka
https://docs.python.org/3/tutorial/
https://github.com
```

## Expected Output

After submitting URLs, the content library should show:

- Saved article cards
- Article titles and descriptions
- Domains
- Extracted images
- Searchable full text
- Generated tags
- Detail views with links and key points
- Analytics for domains, views, and tags

## Why This Project Matters

This project demonstrates a practical architecture used in real systems where ingestion and processing should not block the user interface.

It combines:

- Content management
- Background job processing
- Message queues
- Web scraping
- Persistent storage
- Search and filtering
- Containerized deployment
- CI/CD concepts

The result is a useful content library and a strong DevOps/distributed-systems learning project.

## Real-World Applications

This project can be extended into:

- Research paper or article library
- News collection dashboard
- Documentation bookmark manager
- Competitive research tracker
- SEO content analysis tool
- Learning resource library
- Knowledge base ingestion system
- Internal company reading list

## Future Scope

Possible improvements:

- Add user accounts and authentication.
- Add collections or folders for organizing articles.
- Add manual tags in addition to generated tags.
- Add article summaries.
- Add full-text PostgreSQL indexes.
- Add duplicate detection by URL and content hash.
- Add retry handling for failed scrape jobs.
- Add dead-letter queue support in Kafka.
- Add domain-based rate limiting.
- Add robots.txt awareness.
- Add worker scaling in Kubernetes.
- Add monitoring with Prometheus and Grafana.
- Add CI tests before Docker image builds.

## Conclusion

Distributed Content Library is a platform for saving and organizing useful web content. It uses scraping only as the first step; the main goal is to create a searchable, taggable, and analyzable library from online resources.

By combining FastAPI, Kafka, a background worker, PostgreSQL, Docker Compose, Jenkins, and Kubernetes manifests, the project demonstrates both a useful application and a realistic distributed-system architecture.
