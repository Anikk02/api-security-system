# 🛡️ TriAnSec – Intelligent API Security Platform

An advanced **behavior-based API protection platform** that provides **real-time threat detection, adaptive enforcement, and seamless SDK integration**.

---

## 🚀 Overview

TriAnSec is not just a middleware — it is a **complete API security platform** consisting of:

* 🔐 Authentication & onboarding system
* 🔑 API key-based integration
* 🧠 Behavior-based security engine
* 📊 Client & admin dashboards
* 📦 Python SDK for plug-and-play usage

---

## 🎯 Problem Statement

> APIs are vulnerable to abuse such as bot traffic, scraping, and brute-force attacks. Traditional systems rely on static rules and lack visibility, adaptability, and integration simplicity.

---

## 💡 Solution

TriAnSec introduces a **plug-and-play security layer**:

```text
Client App → TrianSec SDK → Security Engine → Decision → Response
```

With a **complete ecosystem**:

* Authentication system for clients
* API key-based access control
* Dashboard for monitoring & control
* Real-time behavioral analysis engine

---

## 🧠 Core Architecture

```text
Client App
   ↓
TriAnSec SDK (Python Library)
   ↓
API Key Authentication
   ↓
Identity Resolver
   ↓
Feature Engine
   ↓
Risk Engine (Rule-Based)
   ↓
Decision Engine
   ↓
Penalty Manager
   ↓
Response + Logs
```

---

## 📦 Python SDK (Plug-and-Play Integration)

### Purpose

Allow clients to integrate TrianSec into their backend with **minimal effort**.

---

### Usage

```python
from triansec import SecurityMiddleware

app.add_middleware(
    SecurityMiddleware,
    api_key="sk_live_xxxxxx"
)
```

---

### What SDK Does

* Sends request data to TrianSec backend
* Attaches API key
* Receives decision (allow/throttle/block)
* Applies response in client app

---

### Key Benefit

```text
Zero security logic required in client backend
```

---

## 🔐 Authentication & Onboarding System

### Features

* Client registration & login
* JWT-based authentication
* API key generation
* Instant onboarding

---

### Flow

```text
Register →
Create Client →
Generate API Key →
Return Credentials →
Client integrates SDK
```

---

### Dual Identity Model

| Identity Type | Purpose            |
| ------------- | ------------------ |
| JWT           | Dashboard access   |
| API Key       | SDK authentication |

---

## 🧬 Multi-Signal Identity System

* API Key (primary identity)
* IP Address
* User-Agent
* Fingerprint (IP + UA)

---

## 🧠 Behavior Intelligence (No ML)

TrianSec uses **real-time rule-based intelligence**:

* Request rate (req/min)
* Burst detection
* Endpoint access patterns
* Error rates
* Repetition & entropy

---

## ⚖️ Adaptive Decision System

Dynamic actions:

* ✅ Allow
* ⚠️ Throttle
* 🚫 Block

Based on:

* Risk score
* Reputation
* Historical behavior

---

## 💬 Explainable Decisions

```json
{
  "action": "block",
  "reason": "Repeated suspicious behavior",
  "risk_score": 0.91
}
```

---

## 🧠 Stateful Intelligence (Redis)

Stores:

* Request history
* Violations
* Reputation scores
* Block states

---

## 🖥️ Dashboard System

### 👤 Client Dashboard

Clients get **full visibility + control**:

---

#### 📍 Live Threat Map

* Visualizes incoming traffic globally
* Shows attack origins in real-time

---

#### 🚨 Threat Monitoring

* Real-time detection of suspicious activity
* Highlights abnormal patterns

---

#### 🧑‍💻 Top Suspicious Users

* Displays **Top 20 risky users**
* Based on:

  * behavior
  * violations
  * reputation

---

#### 📜 Recent Activity Logs

* Request logs include:

  * action (allow / throttle / block)
  * risk score
  * endpoint
  * timestamp

---

#### 🎛️ Manual Controls

* Block / Unblock any user instantly
* Override system decisions when needed

---

#### 🔑 API Key Management

* Generate API keys
* Revoke compromised keys
* Monitor usage


---

### 🛠️ Admin Dashboard

Admins can:

* Monitor all clients
* Detect system-wide attacks
* View global metrics
* Override policies
* Debug decision pipeline

---

## ⚙️ Tech Stack

### Backend

* FastAPI (async)

### State

* Redis (real-time decision system)

### Database

* PostgreSQL (clients, API keys)

### Frontend

* React.js

### SDK

* Python package (`triansec`)

---

## 📁 Project Structure

```bash
triansec/
├── backend/
│   └── app/
│       ├── middleware/
│       ├── identity/
│       ├── features/
│       ├── risk/
│       ├── policy/
│       ├── state/
│       ├── explainability/
│       ├── auth/
│       ├── client/
│       ├── api_keys/
│       └── main.py
│
├── sdk/              # Python library (triansec)
├── frontend/         # dashboards
├── scripts/
└── docs/
```

---

## 🔄 How It Works

1. Client integrates SDK
2. Request passes through middleware
3. Identity is resolved
4. Features are extracted
5. Risk score is computed
6. Decision is made
7. Response is returned instantly
8. State is updated asynchronously

---

## 📈 Use Cases

* SaaS platforms (API abuse protection)
* Fintech (fraud-like behavior detection)
* AI APIs (cost protection)
* E-commerce (bot prevention)

---

## ⚠️ Scope Clarification

This system:

✅ Provides intelligent API protection
✅ Offers SDK + dashboard ecosystem
❌ Does NOT replace WAF/CDN (Cloudflare, etc.)

---

## 🔮 Future Enhancements

* Background behavior analysis pipeline
* Advanced fingerprinting
* Multi-region deployment
* SaaS hosting model

---

## 👨‍💻 Author

**Aniket Paswan**
B.Tech CSE | AI Systems & Backend Engineering

---

## ⭐ Final Philosophy

```text
Fast Decisions > Heavy Computation
Real-Time State > Offline Models
Integration Simplicity > Complex Setup
```

---

**End of Document**
