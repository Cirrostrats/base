# 🚀 Complete Observability & Running Guide

Production-ready observability with **traces**, **metrics**, and **logs** fully correlated.

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [How to Run](#-how-to-run)
3. [What is Observability?](#-what-is-observability)
4. [Architecture](#-architecture)
5. [Access Points](#-access-points)
6. [Query Guide](#-query-guide)
7. [Troubleshooting](#-troubleshooting)

---

## 🏃 Quick Start

### Start Everything (Easiest)

```bash
cd /Users/harshv/Projects/base
./start-all.sh
```

This starts:
- ✅ Observability Stack (Grafana, Prometheus, Loki, Tempo)
- ✅ Application Stack (Frontend, Backend, Nginx)
- ✅ Shows health checks and access URLs

### Access Grafana

```
http://localhost:3000
Login: admin / admin
```

Go to: **Dashboards → Cirrostrats → Service Overview**

---

## 🎯 How to Run

You have **two separate Docker Compose stacks** that communicate via a shared network.

### Architecture

```
┌─────────────────────────────────────────┐
│   Application Stack                      │
│   (docker-compose.yml)                   │
│   - Frontend (port 5173)                 │
│   - Backend (port 8000)                  │
│   - Nginx (port 80)                      │
└──────────┬──────────────────────────────┘
           │
           │ cirrostrats-network (shared)
           │
┌──────────┴──────────────────────────────┐
│   Observability Stack                    │
│   (cirrostrats-backend/observability/)   │
│   - Grafana (port 3000)                  │
│   - Prometheus (port 9090)               │
│   - Loki (port 3100)                     │
│   - Tempo (port 3200)                    │
└──────────────────────────────────────────┘
```

### Option 1: Use Helper Script (Recommended)

```bash
# Start both stacks
./start-all.sh

# Stop both stacks
./stop-all.sh
```

### Option 2: Manual Start (Everything)

```bash
# 1. Create shared network (if not exists)
docker network create cirrostrats-network

# 2. Start observability stack
cd cirrostrats-backend
docker-compose -f observability/docker-compose.observability-only.yml up -d
cd ..

# 3. Start application stack
docker-compose up -d
```

### Option 3: Only Backend + Observability (No Frontend)

```bash
# 1. Start observability stack
cd cirrostrats-backend
docker-compose -f observability/docker-compose.observability-only.yml up -d
cd ..

# 2. Start only backend
docker-compose up -d backend
```

### Stopping Services

```bash
# Stop application
docker-compose down

# Stop observability
cd cirrostrats-backend
docker-compose -f observability/docker-compose.observability-only.yml down
cd ..
```

Or use: `./stop-all.sh`

---

## 🔍 What is Observability?

Observability is the ability to understand what's happening inside your system by examining its outputs.

### The Three Pillars

```
┌──────────────────────────────────────────────────────┐
│                  OBSERVABILITY                        │
├──────────────┬──────────────┬────────────────────────┤
│ 📊 METRICS   │ 📝 LOGS      │ 🔍 TRACES              │
│              │              │                        │
│ What? When?  │ What went    │ Where did time go?     │
│ How many?    │ wrong? Why?  │ What called what?      │
└──────────────┴──────────────┴────────────────────────┘
```

### Real Example: "Search is slow"

1. **Metrics** → `p95 latency increased from 200ms to 2s at 14:30`
2. **Logs** → Search errors at 14:30 → `"MongoDB timeout trace_id: abc123"`
3. **Traces** → Click trace_id → MongoDB query took 1.8s out of 2s
4. **Root Cause** → MongoDB query missing index

**Result:** Debug in 2 minutes instead of 2 hours!

---

## 📦 Architecture

### Data Flow

```
┌────────────────────────────────────────────┐
│           USER REQUEST                      │
│        curl localhost:8000/search           │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│         FastAPI Backend                     │
│  (Auto-instrumented with OpenTelemetry)    │
│                                             │
│  ├─ Generates trace_id/span_id             │
│  ├─ Adds to logs                            │
│  └─ Exports to OTel Collector               │
└─────────┬───────────────────┬───────────────┘
          │                   │
          │ Metrics           │ Traces/Logs
          ▼                   ▼
┌─────────────────┐  ┌──────────────────────┐
│   Prometheus    │  │  OTel Collector      │
│  (Scrapes /     │  │  (Receives traces    │
│   metrics)      │  │   & logs)            │
└─────────────────┘  └──────┬───────────────┘
                            │
                   ┌────────┴────────┐
                   ▼                 ▼
            ┌──────────┐      ┌──────────┐
            │  Tempo   │      │   Loki   │
            │ (Traces) │      │  (Logs)  │
            └──────────┘      └──────────┘
                   │                 │
                   └────────┬────────┘
                            ▼
                    ┌──────────────┐
                    │   Grafana    │
                    │ (Dashboards) │
                    └──────────────┘
```

### How Communication Works

1. **Backend → OTel Collector**: Backend sends traces to `http://otel-collector:4317` (via shared network)
2. **Prometheus → Backend**: Prometheus scrapes `http://backend:8000/metrics` (via shared network)
3. **Promtail → Backend**: Collects Docker logs from backend container
4. **All data → Grafana**: Unified view of metrics, logs, and traces

---

## 🌐 Access Points

### Application
- **Backend**: http://localhost:8000
- **Backend Health**: http://localhost:8000/health
- **Backend Metrics**: http://localhost:8000/metrics
- **Frontend**: http://localhost:5173
- **Nginx**: http://localhost:80

### Observability
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Tempo**: http://localhost:3200

---

## 📊 Query Guide

### Prometheus (PromQL) Queries

**Basic Metrics:**
```promql
# Request rate (requests per second)
rate(http_requests_total[1m])

# Total requests
sum(http_requests_total)

# Requests by endpoint
sum by (handler) (http_requests_total)
```

**Error Monitoring:**
```promql
# Error rate (5xx errors)
sum(rate(http_requests_total{status=~"5.."}[1m]))

# Error percentage
sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m])) * 100

# 4xx vs 5xx errors
sum by (status) (rate(http_requests_total{status=~"[45].."}[5m]))
```

**Latency Analysis:**
```promql
# p95 latency (milliseconds)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000

# p99 latency
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000

# Average latency by endpoint
avg by (handler) (rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))
```

**Advanced Queries:**
```promql
# Top 5 slowest endpoints
topk(5, histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le)))

# Request rate by status code
sum by (status) (rate(http_requests_total[1m]))

# Throughput (requests per minute)
sum(increase(http_requests_total[1m]))
```

### Loki (LogQL) Queries

**Basic Log Queries:**
```logql
# All backend logs
{container_name="cirrostrats-backend"}

# Logs from last 5 minutes
{container_name="cirrostrats-backend"} [5m]

# Filter by log level
{container_name="cirrostrats-backend"} | json | level="ERROR"

# Search for specific text
{container_name="cirrostrats-backend"} |= "MongoDB"
```

**Structured Log Queries:**
```logql
# Parse JSON logs
{container_name="cirrostrats-backend"} | json

# Filter by HTTP method
{container_name="cirrostrats-backend"} | json | http_method="POST"

# Find slow requests
{container_name="cirrostrats-backend"} | json | latency_ms > 500

# Find specific trace
{container_name="cirrostrats-backend"} | json | trace_id="abc123"
```

**Aggregation Queries:**
```logql
# Count errors per minute
sum(count_over_time({container_name="cirrostrats-backend"} | json | level="ERROR" [1m]))

# Error rate
sum(rate({container_name="cirrostrats-backend"} | json | level="ERROR" [5m]))

# Average latency
avg_over_time({container_name="cirrostrats-backend"} | json | unwrap latency_ms [5m])

# p95 latency from logs
quantile_over_time(0.95, {container_name="cirrostrats-backend"} | json | unwrap latency_ms [5m])
```

**Advanced Filtering:**
```logql
# Logs with errors AND specific endpoint
{container_name="cirrostrats-backend"} | json | level="ERROR" | http_path="/search"

# Multiple conditions
{container_name="cirrostrats-backend"} | json | status_code >= 500 | latency_ms > 1000

# Pattern matching
{container_name="cirrostrats-backend"} | json | message =~ "timeout|error|failed"
```

### Tempo (TraceQL) Queries

**Basic Trace Queries:**
```traceql
# All traces for your service
{service.name="cirrostrats-backend-api"}

# Traces in last 5 minutes
{service.name="cirrostrats-backend-api" && timeRange="5m"}

# Traces with errors
{status=error}

# Slow traces
{duration > 500ms}
```

**Span-Level Queries:**
```traceql
# Find specific spans
{span.name="mongodb.find"}

# HTTP GET requests
{span.http.method="GET"}

# Slow database queries
{span.db.system="mongodb" && duration > 100ms}

# Failed Redis operations
{span.name="redis.get" && status=error}
```

**Advanced Queries:**
```traceql
# Slow POST requests
{span.http.method="POST" && duration > 1s}

# Traces with specific endpoint
{span.http.route="/search"}

# Database operations by collection
{span.db.mongodb.collection="flights"}

# Combine multiple conditions
{service.name="cirrostrats-backend-api" && span.http.status_code >= 500 && duration > 200ms}
```

---

## 🛠️ Troubleshooting

### Backend Can't Connect to OTel Collector

**Error:** `Connection refused to otel-collector:4317`

**Fix:**
```bash
# Check observability stack is running
cd cirrostrats-backend
docker-compose -f observability/docker-compose.observability-only.yml ps

# Check shared network exists
docker network inspect cirrostrats-network

# Restart backend
cd ..
docker-compose restart backend
```

### Prometheus Not Scraping Backend

**Check Prometheus targets:**
```bash
open http://localhost:9090/targets
```

Should show: `backend:8000` with status `UP`

**If down:**
```bash
# Verify both on shared network
docker network inspect cirrostrats-network

# Should see: otel-collector, prometheus, cirrostrats-backend
```

### Dashboard Not Showing Data

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Generate traffic:**
   ```bash
   for i in {1..20}; do curl http://localhost:8000/; done
   ```

3. **Check Prometheus has data:**
   - Open http://localhost:9090
   - Query: `http_requests_total`
   - Should show results

4. **Refresh Grafana dashboard**

### Logs Not Appearing in Loki

Promtail only collects logs from **Docker containers**.

**If running backend locally** (not in Docker):
- Logs appear in terminal, not in Loki
- Use observability stack + backend in Docker instead

### Start Fresh

```bash
# Stop everything
./stop-all.sh

# Remove all containers and volumes
docker-compose down -v
cd cirrostrats-backend
docker-compose -f observability/docker-compose.observability-only.yml down -v
cd ..

# Remove network
docker network rm cirrostrats-network

# Start again
./start-all.sh
```

### Network Issues

**Error:** `network cirrostrats-network not found`

```bash
docker network create cirrostrats-network
```

**Remove and recreate:**
```bash
docker network rm cirrostrats-network
docker network create cirrostrats-network
```

---

## 🎓 Key Concepts

### Trace Context Propagation

Every request gets:
- **trace_id**: Unique ID for entire request flow
- **span_id**: Unique ID for each operation within trace

These IDs are automatically:
- Added to logs → Find all logs for a request
- Sent to Tempo → Visualize request timeline
- Propagated to downstream services → End-to-end tracing

### Tail Sampling (Smart Sampling)

OTel Collector uses tail sampling:
- **100% of errors** → Never miss failures
- **100% of slow requests** → Catch performance issues
- **10% of normal requests** → Reduce storage costs

### Metrics Cardinality

Avoid high-cardinality labels:
- ❌ `user_id` (millions of values)
- ❌ `trace_id` (unique per request)
- ✅ `endpoint` (small set of values)
- ✅ `status_code` (small set of values)

---

## 📁 File Structure

```
/Users/harshv/Projects/base/
├── docker-compose.yml                # Main app stack
├── start-all.sh                      # Start everything
├── stop-all.sh                       # Stop everything
├── OBSERVABILITY-GUIDE.md            # This file
│
├── cirrostrats-backend/
│   ├── observability/
│   │   ├── docker-compose.observability-only.yml
│   │   ├── prometheus-config-shared-network.yml
│   │   ├── loki-config.yml
│   │   ├── tempo-config.yml
│   │   ├── otel-collector-config.yml
│   │   └── grafana/provisioning/
│   │       ├── datasources/
│   │       └── dashboards/
│   └── main.py                       # Backend with OpenTelemetry
│
└── cirrostrats-frontend/
```

---

## 🚀 Next Steps

1. **Start the stack:**
   ```bash
   ./start-all.sh
   ```

2. **Open Grafana:** http://localhost:3000

3. **View dashboard:** Dashboards → Cirrostrats → Service Overview

4. **Generate traffic:**
   ```bash
   curl http://localhost:8000/health
   ```

5. **Explore data:**
   - Metrics: Grafana → Explore → Prometheus
   - Logs: Grafana → Explore → Loki
   - Traces: Grafana → Explore → Tempo

---

## 💡 Tips

- **Correlation is key**: Use trace_id to jump from logs → traces → metrics
- **Start with RED method**: Rate, Errors, Duration
- **Use dashboards**: Pre-built dashboard has everything you need
- **Tail sampling saves money**: Only stores important traces
- **Separate stacks**: Restart backend without restarting Grafana

---

**Need help?** Check troubleshooting section or see logs:
```bash
docker logs -f cirrostrats-backend
docker logs -f grafana
docker logs -f prometheus
```
