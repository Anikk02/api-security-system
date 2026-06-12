# 🔐 Authentication & Onboarding System (TrianSec)

---

## 📌 Overview

This module provides:

* Client authentication (JWT-based)
* Password management (login + reset)
* Client onboarding (API key generation)
* API key management for SDK integration

It integrates seamlessly with the **TrianSec Security Engine** without duplicating core infrastructure.

---

## 🧠 Design Philosophy

* Extend existing backend (no duplication)
* Feature-based architecture
* Separation of business logic & security engine
* Plug-and-play onboarding

---

## 🏗️ System Architecture

```
User (Client)
   ↓
Auth API (Register/Login/Reset)
   ↓
JWT Token
   ↓
Dashboard Access

Client Backend
   ↓
triansec SDK
   ↓
API Key
   ↓
TrianSec Middleware
   ↓
Security Engine
```

---

## 📁 Folder Structure (BACKEND)

```
app/
│
├── authentication/
│   ├── service.py        # register, login, reset password
│   ├── password.py       # hashing & verification
│   ├── token.py          # JWT + reset tokens
│   └── routes.py         # /api/auth/*
│
├── client/
│   ├── service.py
│   ├── onboarding.py
│   └── routes.py
│
├── api_keys/
│   ├── service.py
│   ├── validator.py
│   └── routes.py
│
# ===== EXISTING ENGINE =====
├── middleware/
├── identity/
├── features/
├── risk/
├── policy/
├── state/
├── explainability/
├── websocket/
# ==========================
│
├── core/
├── db/
│   └── models/
        |___client.py
        |___api_key.py
├── schemas/
     |___ auth.py
     |___ client.py
     |___ api_key.py
└── main.py
```
## FOLDER STRUCTURE (FRONTEND)
```text
src/
│
├── pages/
│   ├── auth/
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── ForgotPassword.jsx
│   │   ├── ResetPassword.jsx
│   │
│   ├── onboarding/
│   │   ├── Welcome.jsx
│   │   ├── ApiKeySetup.jsx
│   │   ├── IntegrationGuide.jsx
│   │   └── Success.jsx
│
├── components/
│   ├── auth/
│   │   ├── LoginForm.jsx
│   │   ├── RegisterForm.jsx
│   │   ├── PasswordInput.jsx
│   │   └── AuthLayout.jsx
│   │
│   ├── onboarding/
│   │   ├── Stepper.jsx
│   │   ├── ApiKeyCard.jsx
│   │   ├── CopyButton.jsx
│   │   └── CodeBlock.jsx
│
├── services/
│   ├── authApi.js
│   ├── onboardingApi.js
│
├── hooks/
│   ├── useAuth.js
│   ├── useOnboarding.js
│
├── context/
│   └── AuthContext.jsx
│
├── layouts/
│   ├── AuthLayout.jsx
│   └── OnboardingLayout.jsx
│
├── utils/
│   ├── validators.js
│   └── token.js
│
└── routes/
    └── AuthRoutes.jsx
```

---

## 🔑 Authentication System

### 1. Registration

**Endpoint**

```
POST /api/auth/register
```

**Flow**

1. Validate input
2. Hash password
3. Create client
4. Trigger onboarding

---

### 2. Login

**Endpoint**

```
POST /api/auth/login
```

**Flow**

1. Verify email + password
2. Generate JWT
3. Return access token

---

### 3. Forgot Password

**Endpoint**

```
POST /api/auth/forgot-password
```

**Flow**

1. Accept email
2. Generate short-lived reset token
3. Return or send reset link

**MVP Note**

* Token can be returned in response or logged
* Email service can be integrated later

---

### 4. Reset Password

**Endpoint**

```
POST /api/auth/reset-password
```

**Flow**

1. Verify reset token
2. Hash new password
3. Update password
4. Invalidate token

---

### 5. JWT Usage

```
Authorization: Bearer <token>
```

Used for:

* Dashboard authentication
* Client identity

---

## 🚀 Onboarding System

### Purpose

Enable instant usability after signup.

---

### Flow

```
Register →
Create Client →
Generate API Key →
Initialize Usage →
Return Credentials
```

---

### Core Logic

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
* Identify traffic in middleware

---

### Format

```
X-API-KEY: sk_live_xxxxxxxx
```

---

### Operations

| Action   | Description             |
| -------- | ----------------------- |
| Generate | Create API key          |
| Validate | Middleware validation   |
| Revoke   | Disable compromised key |

---

### Validation Flow

```
Request →
Extract API Key →
Validate →
Attach client_id →
Pass to security engine
```

---

## 🧾 Database Schema

### Clients

```
id
email
password_hash
status
created_at
```

---

### API Keys

```
id
client_id
key
is_active
created_at
```

---

## 🔄 Integration with Security Engine

```
Client App →
triansec SDK →
API Key →
Middleware →
Risk Engine →
Policy Engine →
Decision
```

---

## ⚡ Key Design Decisions

### 1. Dual Identity System

| Type    | Purpose           |
| ------- | ----------------- |
| JWT     | User (dashboard)  |
| API Key | Application (SDK) |

---

### 2. No Duplicate Infrastructure

* Uses existing `core`, `db`, `middleware`
* No separate app
* No extra main.py

---

### 3. Feature-Based Architecture

```
auth/
client/
api_keys/
```

---

## 🧠 Summary

This system:

* Integrates cleanly into your backend
* Keeps security engine untouched
* Enables SaaS layer (clients + dashboard)
* Supports plug-and-play SDK usage

---

## 🚀 Next Steps

* Implement auth APIs
* Implement onboarding flow
* Integrate API key validator into middleware
* Connect client dashboard

---

## 🔥 Final Principle

```
Security Engine = Brain  
Authentication = Entry Layer  
API Keys = Bridge to Client Systems  
```

---

**End of Document**
