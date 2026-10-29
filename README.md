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


******************************************************************************************************
******************************************************************************************************


# Break a Distributed System on Purpose

A hands-on distributed systems experiment exploring the **CAP theorem, data replication, network partitions, and consistency–availability trade-offs** through a containerized, three-node key-value store.

## Overview

Distributed systems must continue operating despite communication failures, node outages, and network partitions. However, when nodes cannot communicate, maintaining consistent data while continuing to accept requests becomes a fundamental design challenge.

This project explores that challenge by building a small distributed key-value store and deliberately disrupting network connectivity between its nodes.

The goal is to move beyond the theoretical explanation of the CAP theorem and observe how different write strategies affect system behavior under failure.

## Architecture

The application consists of three Flask-based nodes running in separate Docker containers. Each node maintains an in-memory key-value store and communicates with its peers over a shared Docker network.

```text
                  Client
                    |
          +---------+---------+
          |         |         |
       Node 1    Node 2    Node 3
       :5001     :5002     :5003
          |         |         |
          +---- Peer Replication ----+
                    |
               Docker Network
```

Each node exposes REST endpoints for reading data, writing data, replicating updates, and switching between operating modes.

## Technology Stack

- **Python** — application logic and node behavior
- **Flask** — REST API endpoints
- **Requests** — inter-node HTTP communication
- **Docker** — containerization
- **Docker Compose** — multi-node orchestration and networking
- **REST APIs / JSON** — client and peer communication

## Key Engineering Concepts

### 1. Consistency-first behavior (CP mode)

In the project's simplified CP mode, a node attempts to replicate a write to all configured peers before committing it locally.

When a peer becomes unreachable, the write is rejected rather than accepted locally.

This demonstrates the availability cost of requiring peer acknowledgments during a network partition.

### 2. Availability-first behavior (AP mode)

In the simplified AP mode, a node commits a write locally and attempts replication on a best-effort basis.

If a peer is unreachable, the write can still succeed. However, isolated nodes may store different values for the same key.

This demonstrates how prioritizing write availability can introduce divergent state.

### 3. Network partition simulation

Docker networking is used to disconnect a node from the cluster without stopping its container.

The same cluster can then be tested under different operating modes to compare:

- Write success and failure behavior
- Replication across reachable peers
- Divergent data during isolation
- Behavior after connectivity is restored

### 4. Failure recovery and reconciliation

Restoring network connectivity does not automatically guarantee that nodes with divergent data will converge.

This highlights an important distinction between **network recovery and data recovery**. A production-grade design needs an explicit strategy for conflict resolution, reconciliation, and convergence.

## Getting Started

### Prerequisites

- Python 3.12 or compatible environment
- Docker Desktop or Docker Engine
- Docker Compose
- `curl` or another REST API client

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd <repository-directory>
```

### 2. Build the Docker images

```bash
docker compose build
```

### 3. Start the cluster

```bash
docker compose up -d
```

### 4. Verify the nodes

```bash
docker compose ps
```

Check the data endpoint of each node:

```bash
curl http://localhost:5001/data
curl http://localhost:5002/data
curl http://localhost:5003/data
```

The default configuration exposes Node 1, Node 2, and Node 3 on ports 5001, 5002, and 5003, respectively.

## API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/data` | Retrieve the node's complete local store |
| GET | `/data/<key>` | Retrieve a value by key |
| PUT | `/data/<key>` | Write a key-value pair |
| POST | `/replicate` | Accept a replication request from a peer |
| GET | `/mode` | Inspect the node's operating mode |
| POST | `/mode` | Switch between CP and AP modes |

All API endpoints are relative to an individual node's address.

## Experiment 1: Observe Normal Replication

Write a value through Node 1:

```bash
curl.exe -X PUT http://localhost:5001/data/color \
  -H "Content-Type: application/json" \
  -d '{\"value\":\"blue\"}'
```

Read the value from all three nodes:

```bash
curl http://localhost:5001/data/color
curl http://localhost:5002/data/color
curl http://localhost:5003/data/color
```

With healthy connectivity and successful replication, the nodes should return the same value.

## Experiment 2: Introduce a Network Partition

Disconnect Node 3 from the shared Docker network:

```bash
docker network disconnect capnet node3
```

In the default CP mode, attempt a write through Node 1:

```bash
curl.exe -X PUT "http://localhost:5001/data/city" -H "Content-Type: application/json" -d '{\"value\": \"London\"}'
```

Because Node 3 is unreachable, the write should be rejected when replication cannot complete.

Reconnect Node 3 after the experiment:

```bash
docker network connect capnet node3
```

The experiment demonstrates how requiring peer acknowledgments affects write availability during a partition.

## Experiment 3: Compare Availability-first Behavior

Switch each node to AP mode while all nodes are reachable:

```bash
curl.exe -X POST http://localhost:5001/mode \
  -H "Content-Type: application/json" \
  -d '{\"mode\":\"AP\"}'

curl.exe -X POST http://localhost:5002/mode \
  -H "Content-Type: application/json" \
  -d '{\"mode\":\"AP\"}'

curl.exe -X POST http://localhost:5003/mode \
  -H "Content-Type: application/json" \
  -d '{\"mode\":\"AP\"}'
```

Disconnect Node 3:

```bash
docker network disconnect capnet node3
```

Now issue writes to reachable nodes while Node 3 is isolated. The writes can succeed locally even when replication cannot reach every peer.

Writing different values for the same key on the isolated and connected sides demonstrates how divergent state can arise.

Reconnect the node when finished:

```bash
docker network connect capnet node3
```

**Note:** This implementation is an educational demonstration. Reconnection alone does not implement automatic reconciliation of divergent data.

## What This Project Demonstrates

- Translating distributed systems theory into executable experiments
- Understanding replication and inter-node communication
- Using container networking to inject controlled failures
- Comparing write behavior under different consistency and availability priorities
- Recognizing the difference between service recovery and data convergence

## Current Scope and Limitations

This project intentionally keeps the implementation small so the behavior can be observed directly.

- Data is stored in memory and is lost when a node process restarts.
- Replication is implemented using synchronous HTTP requests.
- The CP/AP modes are simplified demonstrations, not complete implementations of production distributed database protocols.
- There is no consensus protocol, durable storage, quorum-based replication, or automatic conflict-resolution mechanism.
- Authentication, authorization, observability, and production deployment hardening are outside the current scope.

These limitations are important when comparing the experiment with production systems.

## Potential Extensions

- Implement timestamp-based conflict resolution.
- Add automatic reconciliation after a network partition heals.
- Introduce quorum-based read and write policies.
- Add automated integration tests for node failures and recovery.
- Add structured logging, health checks, metrics, and failure-injection tests.
- Explore durable storage and compare replication strategies.

## Learning Reference

This project was completed as a hands-on learning exercise inspired by the NextWork project:

[Break a Distributed System on Purpose](https://nextwork.ai/projects/56330f0f-e0c6-474e-bda9-d625ff412ba0)

The implementation is intended for educational use and further experimentation with distributed systems fundamentals.
