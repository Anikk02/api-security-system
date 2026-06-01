# 🔐 Authentication & Onboarding System (TrianSec)

## 📌 Overview

This module handles:

* Client registration & login
* JWT-based authentication
* API key generation for SDK integration
* Initial onboarding of new clients

It is designed to work alongside the **TrianSec Security Engine**, keeping business logic separate from security logic.

---

## 🧠 System Design Principles

* **Separation of concerns**
* **Stateless authentication (JWT)**
* **API key-based SDK access**
* **Fast onboarding (plug-and-play)**

---

## 🏗️ Architecture Flow

```
Client (User)
   ↓
Auth API (Register/Login)
   ↓
JWT Issued
   ↓
Client Dashboard Access

Client Backend
   ↓
triansec SDK
   ↓
API Key
   ↓
TrianSec Security Engine
```

---

## 📁 Module Structure

```
app/
│
├── core/                          # Core system config
│   ├── config.py
│   ├── security.py                # JWT, hashing, auth helpers
│   ├── dependencies.py            # Auth dependencies (get_current_user)
│   └── constants.py
│
├── db/
│   ├── session.py
│   └── models/
│       ├── client.py              # clients table
│       ├── api_key.py             # api_keys table
│       └── usage.py               # usage tracking (basic)
│
├── schemas/                       # Request/Response validation
│   ├── auth.py
│   ├── client.py
│   ├── api_key.py
│   └── usage.py
│
├── repositories/                  # DB access layer
│   ├── client_repo.py
│   ├── api_key_repo.py
│   └── usage_repo.py
│
├── services/                      # Business logic (IMPORTANT)
│   │
│   ├── auth/
│   │   ├── auth_service.py        # register, login
│   │   ├── password_service.py
│   │   ├── token_service.py       # JWT handling
│   │   └── email_service.py       # optional (verification/reset)
│   │
│   ├── client/
│   │   ├── client_service.py      # client CRUD
│   │   ├── onboarding_service.py  # onboarding pipeline
│   │   └── profile_service.py
│   │
│   ├── api_keys/
│   │   ├── api_key_service.py     # create/revoke keys
│   │   └── key_validator.py       # used by middleware
│   │
│   └── usage/
│       └── usage_service.py       # track client usage (basic)
│
├── api/                           # FastAPI routes
│   │
│   ├── auth/
│   │   └── routes.py              # /api/auth/*
│   │
│   ├── client/
│   │   └── routes.py              # /api/client/*
│   │
│   ├── api_keys/
│   │   └── routes.py
│   │
│   └── usage/
│       └── routes.py
│
├── middleware/                    # Your existing system (keep as-is)
│   └── request_middleware.py
│
├── utils/
│   ├── logger.py
│   ├── validators.py
│   └── helpers.py
│
└── main.py
```

---

## 🔑 Authentication System

### 1. Registration

**Endpoint:**

```
POST /api/auth/register
```

**Flow:**

1. Validate input (email, password)
2. Hash password
3. Create client record
4. Trigger onboarding process

---

### 2. Login

**Endpoint:**

```
POST /api/auth/login
```

**Flow:**

1. Verify email + password
2. Generate JWT token
3. Return access token

---

### 3. JWT Token

Used for:

* Dashboard authentication
* Client identity verification

**Stored in:**

```
Authorization: Bearer <token>
```

---

## 🚀 Onboarding System

### Purpose

Automatically prepare a new client to start using TrianSec immediately.

---

### Onboarding Steps

```
Register →
Create Client →
Generate API Key →
Initialize Usage →
Return Credentials
```

---

### Core Function

```python
async def onboard_client(data):
    client = await create_client(data)
    
    api_key = await create_api_key(client.id)
    
    await initialize_usage(client.id)
    
    return {
        "client": client,
        "api_key": api_key
    }
```

---

## 🔐 API Key System

### Purpose

* Authenticate client applications
* Enable SDK integration
* Track usage per client

---

### API Key Format

```
X-API-KEY: sk_live_xxxxxxxx
```

---

### Operations

| Action   | Description             |
| -------- | ----------------------- |
| Generate | Create new API key      |
| Validate | Used in middleware      |
| Revoke   | Disable compromised key |

---

### Validation Flow

```
Request →
Extract API Key →
Validate →
Attach client_id →
Proceed to security engine
```

---

## 🧾 Database Schema (Minimal)

### Clients Table

```
id
email
password_hash
status
created_at
```

---

### API Keys Table

```
id
client_id
key
is_active
created_at
```

---

### Usage Logs

```
client_id
date
request_count
```

---

## 🔄 Integration with Security Engine

After authentication:

```
Client App →
triansec SDK →
API Key →
Security Middleware →
Your Existing System
```

---

## ⚡ Key Design Decisions

### 1. Dual Identity Model

| Type    | Purpose            |
| ------- | ------------------ |
| JWT     | Client (dashboard) |
| API Key | Application (SDK)  |

---

### 2. Fast Middleware Access

Middleware should:

* Validate API key
* Fetch client_id
* Pass to security system

---

### 3. Minimal Initial Scope

For now, system includes:

* Authentication
* Onboarding
* API keys
* Basic usage tracking

**Excluded:**

* Billing
* Subscriptions
* Advanced analytics

---

## 🧠 Summary

TrianSec Authentication & Onboarding provides:

* Seamless client onboarding
* Secure authentication via JWT
* Plug-and-play SDK integration via API keys
* Clean separation from security logic

---

## 🚀 Next Steps

* Build auth APIs
* Implement onboarding_service
* Integrate API key validation into middleware
* Connect client dashboard

---

**End of Document**
