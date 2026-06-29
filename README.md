# 🛡️ API Security System

A scalable, behavior-driven API security platform that protects backend business logic from abuse using real-time behavioral analysis, adaptive policy decisions, reputation tracking, and explainable enforcement.

---

# 🚀 Overview

Modern APIs face attacks that cannot be effectively mitigated using fixed rate limits or simple request counters. Credential stuffing, scraping, automated bots, API abuse, and business workflow attacks often resemble legitimate traffic, making static protection insufficient.

The API Security System introduces an intelligent middleware layer that evaluates every incoming request before it reaches application business logic.

Instead of asking:

> **"Has this request exceeded a fixed limit?"**

the system asks:

> **"Given the request's behavior, identity history, reputation, and current context, should this request be allowed?"**

This approach improves security while minimizing false positives for legitimate users.

Unlike traditional middleware libraries, this project is designed as a **complete API security platform**. In addition to the core behavior analysis engine, it includes an authentication system, API key management, client and administrator dashboards, and a Python SDK that enables seamless integration into existing backend applications.

---

# 🎯 Design Goals

The system is designed to:

* Protect backend business logic from abuse
* Reduce false positives compared to traditional rate limiters
* Adapt to each client's traffic patterns
* Provide transparent and explainable decisions
* Scale across multiple tenants
* Maintain low-latency request processing
* Simplify integration through a plug-and-play SDK
* Centralize security logic outside client applications

---

# 🏗️ Architecture

```text
                    Incoming Request
                            │
                            ▼
                        Python SDK
                            │
                            ▼
                API Key Authentication
                            │
                            ▼
                 Identity Resolution
                            │
                            ▼
                 Feature Engineering
                            │
                            ▼
                  Analysis Pipeline
                            │
                            ▼
                     Policy System
                            │
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
   Trust Engine      Threshold Engine     Recovery Engine
                            │
                            ▼
                    Policy Decision
                            │
                            ▼
              ALLOW / THROTTLE / BLOCK
                            │
                            ▼
                    Business Logic
```

The security engine executes before application business logic, ensuring that potentially abusive traffic is filtered before consuming backend resources.

---

# 🔌 Python SDK

To simplify adoption, the platform provides a lightweight Python SDK that integrates directly with FastAPI applications through middleware.

Example:

```python
from triansec import SecurityMiddleware

app.add_middleware(
    SecurityMiddleware,
    api_key="sk_live_xxxxxxxxx"
)
```

The SDK automatically:

* Authenticates requests using the client's API key
* Sends request metadata to the security engine
* Receives policy decisions in real time
* Applies ALLOW, THROTTLE, or BLOCK responses
* Requires minimal integration code

### SDK Philosophy

```text
Zero security logic required in the client application.
```

Application developers only integrate the middleware, while all behavioral analysis, policy evaluation, reputation tracking, and enforcement remain centralized within the security platform.

---

# ✨ Core Features

## Behavior-Driven Protection

Instead of relying on static request limits, the system continuously evaluates behavioral signals including:

* Request frequency
* Historical activity
* Reputation
* Identity characteristics
* Request timing patterns
* Endpoint access behavior

---

## Adaptive Policy Engine

Every request is evaluated using contextual information rather than predefined request limits.

Possible actions include:

* ✅ Allow
* ⚠️ Throttle
* ⛔ Block

The enforcement adapts to observed behavior rather than static thresholds.

---

## Multi-Signal Identity Resolution

Each request is evaluated using multiple identity signals.

### Primary Identity

* API Key (Tenant)

### Additional Signals

* IP Address
* User-Agent
* Request Path
* HTTP Method
* Timing Patterns
* Generated Fingerprint (IP + User-Agent)

Using multiple identity signals allows the platform to detect suspicious behavior even when attackers rotate IP addresses or modify request headers.

---

## Reputation Tracking

The system maintains historical reputation for multiple entities including:

* API identities
* IP addresses
* Fingerprints

Historical behavior influences future policy decisions, enabling progressive enforcement while allowing recovery after sustained legitimate activity.

---

## Trust-Based Decision Making

Instead of relying solely on counters, requests are evaluated using a dynamic trust score derived from:

* Current request risk
* Historical reputation
* Request volume
* Previous violations
* Error history
* IP rotation patterns
* Recovery history

The resulting trust score is converted into a policy decision through adaptive thresholds.

---

## Explainable Decisions

Every enforcement action includes an explanation describing why the decision was made.

Example:

```json
{
  "action": "BLOCK",
  "trust_score": 0.24,
  "suspicion_score": 0.76,
  "risk_score": 0.91,
  "reason": [
    "High request burst",
    "Poor historical reputation",
    "Multiple previous violations"
  ]
}
```

Explainable responses help developers understand security decisions, simplify debugging, and reduce operational uncertainty.

---

## Progressive Enforcement

Rather than immediately blocking suspicious users, the system gradually escalates responses.

```text
Normal Behavior
        │
        ▼
     ALLOW
        │
        ▼
Suspicious Activity
        │
        ▼
   THROTTLE
        │
        ▼
Repeated Abuse
        │
        ▼
     BLOCK
```

This balances strong security with a positive experience for legitimate users.

---

## Multi-Tenant Architecture

Each client operates independently through API-key isolation.

The system maintains separate:

* Reputation
* Request history
* Analytics
* Policy decisions
* Threshold adaptation

for every tenant, ensuring that one client's traffic never influences another client's security posture.

---

# 🔐 Authentication & Onboarding

The platform includes a secure authentication and onboarding system that enables clients to register, obtain API credentials, and integrate the security platform with minimal effort.

## Features

* Client registration
* Client login
* JWT-based authentication
* Secure API key generation
* API key rotation
* API key revocation
* Instant onboarding

---

## Onboarding Flow

```text
Register
    │
    ▼
Create Client
    │
    ▼
Generate API Key
    │
    ▼
Receive Credentials
    │
    ▼
Integrate Python SDK
    │
    ▼
Protected API
```

This workflow allows developers to protect their APIs without modifying their existing business logic.

---

## 🔑 API Key Management

The platform provides secure lifecycle management for API credentials.

Supported operations include:

* Generate new API keys
* Rotate API keys
* Revoke compromised API keys
* View API key usage statistics
* Monitor authentication activity

Each API key uniquely identifies a client (tenant) and is used by the SDK to authenticate requests before they enter the behavioral analysis pipeline.

---

# 🧬 Identity Resolution

Every incoming request is evaluated using multiple identity signals rather than relying on a single identifier.

## Primary Identity

* API Key (Tenant)

## Additional Identity Signals

* IP Address
* User-Agent
* Request Path
* HTTP Method
* Request Timing
* Generated Fingerprint (IP + User-Agent)

By correlating multiple identity signals, the platform can continue tracking suspicious actors even when they rotate IP addresses or modify request headers. This significantly improves detection accuracy while reducing false positives for legitimate users.

---

# 🧠 Stateful Intelligence

Unlike traditional stateless middleware, the platform continuously maintains historical behavioral state for every client.

Redis serves as the real-time state engine and stores:

* Request history
* Sliding request windows
* Reputation scores
* Violation counters
* Temporary block states
* Burst detection data
* Recovery history
* Adaptive policy state

Maintaining historical state enables the security engine to evaluate requests using both current behavior and long-term behavioral context, resulting in more accurate policy decisions.

---

# 📊 Dashboard

The platform provides dedicated dashboards for both clients and administrators, offering visibility into API activity, security events, and behavioral analytics.

---

## 👤 Client Dashboard

Clients receive comprehensive monitoring and management capabilities for their protected APIs.

### Dashboard Features

* System health overview
* Traffic distribution
* Requests per second (RPS)
* Policy decision trends
* Violation statistics
* Suspicious sessions
* Top suspicious users
* Risk score trends
* Peak attack times
* Spike correlation analysis
* Endpoint analytics
* API key management
* Policy decision logs
* Activity timeline
* User investigation pages

---

### 🌍 Live Threat Map

Visualizes incoming API traffic geographically, helping identify attack origins and suspicious regions in real time.

---

### 🚨 Real-Time Threat Monitoring

Continuously detects abnormal traffic behavior such as:

* Request bursts
* Credential stuffing attempts
* Automated scraping
* Endpoint abuse
* Suspicious behavioral patterns

---

### 👥 Top Suspicious Users

Displays the highest-risk identities based on:

* Trust score
* Reputation
* Violation history
* Request frequency
* Behavioral analysis

This allows clients to quickly investigate potentially malicious users.

---

### 📜 Request & Decision Logs

Every processed request includes detailed information such as:

* Timestamp
* Endpoint
* HTTP method
* Policy decision
* Trust score
* Risk score
* Identity information
* Decision explanation

These logs simplify auditing, debugging, and incident investigation.

---

### 🎛️ Manual Controls

Clients can manually override automated decisions whenever necessary.

Supported actions include:

* Block user
* Unblock user
* Reset reputation
* Review recent activity

Manual controls provide additional flexibility during incident response.

---

# 🛠️ Admin Dashboard

Administrators have a platform-wide view of all tenants and system activity.

Capabilities include:

* Monitor all registered clients
* Observe global traffic
* Detect platform-wide attack campaigns
* View aggregated analytics
* Override security policies
* Investigate suspicious tenants
* Debug policy decisions
* Monitor overall platform health

---

# ⚙️ Technology Stack

## Backend

* FastAPI
* Python

---

## Data Storage

### Redis

Used for:

* Real-time behavioral state
* Reputation tracking
* Request history
* Sliding windows
* Temporary enforcement state

### PostgreSQL

Used for persistent storage of:

* Client accounts
* API keys
* Authentication data
* Audit logs
* Analytics
* Dashboard data

---

## Frontend

* React
* Chart.js / Recharts

---

## Infrastructure

* Docker

---

# 📁 Project Structure

```text
api-security-system/

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
├── sdk/                  # Python SDK
├── frontend/
├── services/
├── worker/
├── docs/
├── scripts/
└── docker/
```
---

# 🔄 Request Lifecycle

Every request follows the same processing pipeline before reaching application business logic.

1. API key authentication
2. Identity resolution
3. Feature extraction
4. Behavioral analysis
5. Trust score calculation
6. Adaptive policy evaluation
7. Recovery state update
8. Policy enforcement
9. Logging and analytics

The security engine performs all behavioral analysis before forwarding approved requests to the protected application, ensuring that suspicious traffic is intercepted early.

---

# 📈 Example Use Cases

The platform is suitable for protecting APIs that expose critical business workflows.

Examples include:

* Authentication endpoints
* Registration APIs
* Password reset
* OTP generation
* Payment processing
* Order management
* User management
* Public APIs
* SaaS platforms
* FinTech services
* E-commerce applications
* AI and LLM APIs
* Internal enterprise APIs
* Developer platforms

---

# 📌 Scope

## ✅ This System Provides

* Behavior-driven API protection
* Business logic protection
* Adaptive policy enforcement
* Multi-tenant request isolation
* Behavioral analytics
* Explainable security decisions
* Historical reputation tracking
* Progressive enforcement
* Real-time monitoring
* API key management
* Dashboard-based visibility
* Plug-and-play SDK integration

---

## ❌ This System Does Not Provide

* DDoS mitigation
* CDN functionality
* Network firewall capabilities
* Web Application Firewall (WAF)
* Infrastructure-level attack protection
* Load balancing
* Reverse proxy functionality

These responsibilities belong to edge security solutions such as Cloudflare, AWS Shield, AWS WAF, or similar infrastructure security services.

The API Security System is designed to operate behind those services, protecting application business logic after requests have reached the application layer.

---

# 🚀 Future Roadmap

Planned enhancements include:

* Pluggable analysis modules
* Enhanced fingerprinting
* Threat intelligence integration
* Distributed deployment
* Multi-region architecture
* Plugin architecture
* Background behavioral analysis pipeline
* Custom security policy framework
* Additional dashboard analytics
* SDK support for more backend frameworks
* SaaS-hosted deployment model

---

# 👥 Contributors

This project is being developed collaboratively by:

| Name                     | Role                                                                                          |
| ------------------------ | --------------------------------------------------------------------------------------------- |
| **Aniket Paswan**        | Backend Architecture, System Design, Policy Engine, Security Middleware, Frontend Development |
| **Anjali Jha**           | Authentication Architecture, API Key Generation & Management, Frontend Development, UI/UX     |
| **Anshika Pratap Singh** | System Management, Frontend Development, UI/UX, Developer Dashboard                           |

---

## Project Ownership

The repository is maintained by **Aniket Paswan**, with contributions from **Anjali Jha** and **Anshika Pratap Singh**.

---

# 👨‍💻 Author

**Aniket Paswan**

Backend Engineering • System Design • API Security

---

# ⭐ Philosophy

The objective of this project is not simply to block requests.

It is to distinguish legitimate users from abusive behavior while minimizing unnecessary disruption to genuine users.

Rather than relying solely on static request limits, the platform continuously evaluates behavioral patterns, historical reputation, identity signals, and contextual information to make adaptive security decisions.

Its design is guided by the following principles:

```text
Fast Decisions > Heavy Computation
Real-Time State > Offline Models
Behavior Intelligence > Static Thresholds
Integration Simplicity > Complex Setup
Explainable Decisions > Black-Box Security
```

The system continuously observes behavioral patterns, learns from historical activity through stateful reputation tracking, and adapts its enforcement strategy to provide strong protection while preserving a seamless experience for legitimate users.
