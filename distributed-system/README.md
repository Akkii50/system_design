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
