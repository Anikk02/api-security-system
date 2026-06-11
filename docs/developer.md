# 🛠️ Developer Control Panel (TrianSec)

---

## 📌 Overview

The **Developer Control Panel** is an internal system designed for:

* Platform administrators
* Backend engineers
* System operators

It provides **global visibility, control, and debugging capabilities** over the entire TrianSec infrastructure.

> ⚠️ This panel is **not accessible to clients** and operates at the **platform level**, not per-client level.

---

## 🎯 Objectives

* Monitor system-wide traffic and behavior
* Detect abuse patterns across clients
* Debug and analyze system decisions
* Manage client access and status
* Ensure system health and reliability

---

## 🧠 Design Principles

* **Centralized Intelligence** → One source of truth
* **Read-heavy architecture** → Observability first
* **Minimal manual control** → Avoid misconfiguration
* **Separation from client view** → No overlap in responsibilities

---

## 🧩 Module Structure

```text
Developer Dashboard
├── Overview
├── Traffic Analytics
├── Abuse Monitoring
├── Logs (Global)
├── Client Management
├── System Health
└── Debug Tools
```

## FOLDER STRUCTURE
```text
app/
├── developer/
│   ├── services/           # Core business logic (IMPORTANT)
│   │   ├── metrics_service.py
│   │   ├── logs_service.py
│   │   ├── clients_service.py
│   │   ├── system_service.py
│   │   └── debug_service.py
│   │
│   ├── schemas/            # Request/response models
│   │   ├── metrics.py
│   │   ├── logs.py
│   │   ├── clients.py
│   │   ├── system.py
│   │   └── debug.py
│   │
│   ├── utils/              # Shared helpers (optional but useful)
│   │   ├── aggregations.py
│   │   └── filters.py
│   │
│   └── __init__.py
```

---

## 🌍 1. Overview

### Purpose

Provide a high-level snapshot of system activity.

---

### Metrics

* Total requests (per minute/hour/day)
* Active clients
* Requests per client (top consumers)
* System throughput

---

## 📊 2. Traffic Analytics

### Purpose

Understand traffic distribution across the platform.

---

### Features

* Requests by endpoint
* Requests by client
* Traffic trends over time
* Load distribution

---

### Insights

* Identify heavily used endpoints
* Detect unusual traffic patterns
* Analyze growth trends

---

## 🚨 3. Abuse Monitoring

### Purpose

Detect and analyze malicious or abnormal behavior globally.

---

### Features

* Top abusive clients
* Most blocked IPs/users
* High-frequency request sources
* Endpoint-level abuse patterns

---

### Example

```text
Client A → 70% of blocked traffic  
Endpoint /login → highest abuse rate  
```

---

## 📜 4. Global Logs

### Purpose

Provide a centralized log system for all clients.

---

### Log Data

* Client ID
* IP address
* Endpoint
* Timestamp
* Action (allow / throttle / block)
* Reason

---

### Capabilities

* Filter by client
* Filter by endpoint
* Filter by action
* Search specific IP/user

---

## 🏢 5. Client Management

### Purpose

Allow administrators to control client access and activity.

---

### Features

* View all registered clients
* Activate / deactivate clients
* Revoke API keys
* Monitor client usage

---

### Actions

* Block client access (system-level)
* Investigate suspicious clients
* Enforce platform policies

---

## ⚡ 6. System Health

### Purpose

Monitor infrastructure and ensure uptime.

---

### Metrics

* API latency
* Error rates
* Database status
* Redis/cache status

---

### Use Cases

* Detect system failures
* Monitor performance bottlenecks
* Ensure availability

---

## 🔍 7. Debug Tools

### Purpose

Provide deep inspection of system behavior.

---

### Features

* Inspect request lifecycle
* View decision reasoning (internal)
* Replay requests (optional future feature)
* Analyze feature computation

---

### Importance

This module is critical for:

* Debugging incorrect decisions
* Understanding system behavior
* Improving detection logic

---

## 🚫 What Developer Panel Does NOT Include

* ❌ Client-specific UI duplication
* ❌ Per-client policy customization
* ❌ Authentication management
* ❌ Manual tuning of detection logic per client

---

## 🧠 Responsibility Boundaries

| Component        | Scope           |
| ---------------- | --------------- |
| Client Dashboard | Per-client view |
| Developer Panel  | Global system   |
| Security Engine  | Internal logic  |

---

## 📈 Scaling Consideration

* Designed for **~1000 clients (MVP)**
* Optimized for **read-heavy operations**
* Aggregation queries must be efficient
* Logging system should support filtering and pagination

---

## 🔐 Access Control

* Restricted to **internal users only**
* Role-based access (future enhancement):

  * Admin
  * Developer
  * Observer

---

## 🔥 Final Principle

```text
Client View → Local Visibility  
Developer View → Global Control  
Security Engine → Core Intelligence  
```

---

**End of Document**
