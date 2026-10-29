# system_design
******************************************************************************************************
******************************************************************************************************
# URL Shortener

A containerized URL shortener built with Flask, PostgreSQL, and Redis, designed to explore efficient URL resolution, persistent storage, caching strategies, and backend service design.

The application generates compact Base62 short codes for submitted URLs and redirects incoming requests to their original destinations. PostgreSQL serves as the persistent data store, while Redis provides a caching layer for frequently accessed mappings.

## Overview

The system implements a straightforward URL shortening workflow with an emphasis on separating persistent storage from the read-optimization layer.

**Key capabilities**

- Generate short codes using Base62 encoding of database-generated identifiers.
- Persist URL mappings in PostgreSQL.
- Cache URL mappings in Redis to accelerate subsequent lookups.
- Resolve cache misses through a PostgreSQL fallback.
- Populate the cache after successful database lookups.
- Validate request payloads and short-code characters.
- Expose a health-check endpoint.
- Run the application and its supporting services using Docker Compose.

## Architecture

```text
                  Client
                    |
          +---------+---------+
          |                   |
       POST /shorten       GET /<code>
          |                   |
          v                   v
        Flask API        Redis Cache
          |              /         \
          |          Cache Hit    Cache Miss
          |              |            |
          |              |            v
          |              |        PostgreSQL
          |              |            |
          |              |       Populate Cache
          |              |            |
          +--------------+------------+
                         |
                    HTTP Redirect
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| Flask | HTTP endpoints, request validation, URL creation, and redirects |
| PostgreSQL | Persistent URL storage and database-generated identifiers |
| Redis | Cached short-code-to-URL mappings |
| Docker Compose | Local orchestration of the application and supporting services |

## Request workflows

### 1. URL creation

1. The client submits a URL to `POST /shorten`.
2. The API validates that the request contains a non-empty `url` field.
3. PostgreSQL stores the original URL and generates a unique numeric ID.
4. The ID is encoded into a Base62 short code.
5. Redis caches the short-code-to-URL mapping.
6. The API returns the generated short URL and short code.

### 2. URL resolution

1. A client requests `GET /<short_code>`.
2. The application checks Redis for the corresponding URL.
3. On a cache hit, the application redirects the client to the original URL.
4. On a cache miss, the application decodes the short code and queries PostgreSQL using the resulting ID.
5. If the mapping exists, the application caches it and issues the redirect.
6. Invalid codes and unknown mappings return a `404` response.

### 3. Short-code generation

The application uses Base62 encoding with the following character set:

`0-9`, `a-z`, `A-Z`

Instead of generating random codes and checking for collisions, the implementation encodes a database-generated numeric identifier. This provides deterministic code generation for the corresponding database ID.

## Technology stack

- **Python** — Application implementation
- **Flask** — HTTP API and redirect handling
- **PostgreSQL** — Persistent relational storage
- **Redis** — In-memory caching
- **Docker** — Application containerization
- **Docker Compose** — Local multi-service orchestration

## Getting started

### Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose
- Git

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd url-shortener
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Configure the services

The application reads database and Redis connection settings from environment variables.

| Variable | Default value |
|---|---|
| `REDIS_HOST` | `redis` |
| `REDIS_PORT` | `6379` |
| `POSTGRES_HOST` | `db` |
| `POSTGRES_DB` | `urlshortener` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `postgres` |

These defaults assume the service names and database configuration used by the Docker Compose setup.

For anything beyond local development, use secure credentials and avoid committing secrets to version control.

### 3. Start the application

From the directory containing `compose.yaml` or `docker-compose.yml`, run:

```bash
docker compose up --build -d
```

Check service status:

```bash
docker compose ps
```

Inspect application logs:

```bash
docker compose logs -f web
```

The examples below assume the application is accessible at `http://localhost:5000`.

## API reference

### Create a short URL

`POST /shorten`

**Request**

```json
{
  "url": "https://example.com/articles/backend-system-design"
}
```

**Successful response — `201 Created`**

```json
{
  "short_url": "http://localhost:5000/1",
  "short_code": "1"
}
```

The actual short code depends on the ID assigned by PostgreSQL. The example assumes the generated ID is `1`.

**Validation error — `400 Bad Request`**

Returned when the JSON body is missing, the `url` field is absent, or the URL is empty.

```json
{
  "error": "Missing url field"
}
```

For an empty URL value:

```json
{
  "error": "URL cannot be empty"
}
```

**Example using curl**

```bash
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

or

```bash
Invoke-RestMethod -Uri "http://localhost:5000/shorten" -Method Post -ContentType "application/json" -Body '{"url": "https://www.youtube.com"}'
```

or

```bash
curl.exe -X POST http://localhost:5000/shorten -H "Content-Type: application/json" -d '{\"url\": \"https://www.google.com\"}'
```

### Redirect to the original URL

`GET /<short_code>`

Example:

```bash
curl -i http://localhost:5000/1
```

A successful lookup returns an HTTP `302 Found` redirect with a `Location` header pointing to the original URL.

The endpoint returns `404 Not Found` when the short code contains unsupported characters or does not correspond to an existing database record.

### Health check

`GET /health`

Example:

```bash
curl http://localhost:5000/health
```

**Response — `200 OK`**

```json
{
  "status": "healthy"
}
```

This endpoint confirms that the Flask application can respond to a request. It does not independently verify PostgreSQL or Redis availability.

## Caching strategy

Redis is used to reduce repeated database lookups during URL resolution.

**Cache hit:** The original URL is retrieved directly from Redis.

**Cache miss:** The application queries PostgreSQL, retrieves the original URL if the record exists, and stores the mapping in Redis for subsequent requests.

This read-through-style lookup flow illustrates a common performance optimization in backend services.

The current implementation does not configure a cache expiration policy or explicit cache invalidation.

## Design considerations and limitations

This implementation is a foundation for exploring backend system design, rather than a production-ready URL shortening service.

Areas worth considering for further development include:

- **URL validation and security:** Validate URL schemes and destinations, and address unsafe redirect destinations.
- **Database connection management:** Introduce connection pooling and robust resource cleanup.
- **Cache resilience:** Handle Redis timeouts and failures without unnecessarily disrupting valid database-backed lookups.
- **Consistency:** Define cache invalidation and expiration policies if URL mappings become editable or deletable.
- **Concurrency:** Review transaction handling and behavior under concurrent requests.
- **Scalability:** Evaluate indexing, database throughput, caching effectiveness, and horizontal application scaling.
- **Observability:** Replace diagnostic prints with structured logging and add meaningful operational metrics.
- **Testing:** Add automated unit, integration, and API tests for success paths and failure scenarios.
- **Deployment security:** Disable Flask debug mode outside local development and manage secrets securely.

These are potential improvements, not capabilities claimed by the current implementation.

## Potential future enhancements

- URL expiration and deletion
- Custom aliases
- Click analytics and usage statistics
- Rate limiting and abuse prevention
- Automated testing with CI
- Structured logging and application metrics
- Load testing and performance benchmarking
- Cloud deployment with managed PostgreSQL and Redis services

## Learning objectives

This project provides a practical way to investigate:

- Identifier generation and Base62 encoding
- REST API design and HTTP redirect semantics
- Relational persistence and database-generated identifiers
- Cache-aside-style read optimization
- Cache misses and database fallback behavior
- Multi-service container orchestration
- Reliability, security, and scalability trade-offs

## License

Add a license file if you intend to distribute this project under an open-source license.
