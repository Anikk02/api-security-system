# 🧍 Identity Resolver (`resolver.py`)

## 📌 Purpose

The Identity Resolver is a multi-tenant gateway component. It assigns a **consistent Tenant Identity** to incoming client applications and isolates, identifies, and tracks the specific **End-Users** interacting with those applications.

---

## ⚙️ Role

* **Identifies the Tenant**: Extracts and validates the client application credentials via the `X-API-KEY` header.
* **Isolates End-User Traffic**: Generates a unique tracking fingerprint for the client's downstream users.
* **Resolves Complex Networks**:
  * Parses multi-tier proxy chains to find the true end-user network source.
  * Tracks the client application server IP address for server-to-server calls.
* **Protects Platform Infrastructure**: Distinguishes between a single bad actor and a high-volume spike from a healthy client application.

---

## 🧱 Structure
## 🧱 Identity Model

```python
class Identity:
    identity_id: str                 # Composite identity (api:<key>:user:<identifier>)
    client_id: int | None            # Tenant (API owner)
    api_key: str | None
    is_anonymous: bool

    ip_address: str | None
    behavioral_fingerprint: str | None
    api_key_id: int |None

    user_identifier_type: str | None
    user_identifier_value: str | None
    is_persistent: bool
```

### Identity Components

The resolver separates **Tenant Identity** from **End-User Identity**.

| Component | Purpose |
|-----------|----------|
| Client ID | Identifies the API customer (tenant) |
| API Key ID | Internal API key record |
| User Identifier | Identifies the downstream user inside that tenant |
| Behavioral Fingerprint | Tracks request behavior |
| IP Address | Network origin |
| Composite Identity | Complete unique identity used throughout the security pipeline |

Example:

```
api:25:user:9d8d66a8-acde...
```

This means:

- API Key #25
- End-user UUID `9d8d66...`

Every downstream security engine uses this composite identity instead of only an IP address.

---

## 👤 End-User Identification

One API key may represent thousands of users.

The resolver therefore performs **per-user identification** inside every authenticated tenant.

### Identification Priority

```
1. Secure Cookie
        ↓
2. JWT Subject/User ID
        ↓
3. IP + User-Agent Fingerprint
        ↓
4. Generated UUID
```

---

### 1. Cookie Identification

If the browser already owns

```
X-TrianSec-User-ID
```

the resolver immediately identifies the user.

Advantages

- Persistent
- Very fast
- Stable across sessions
- Independent of IP changes

---

### 2. JWT Identification

If the client application sends

```
Authorization: Bearer <token>
```

the resolver attempts to extract

```
sub
```

or another configured user identifier.

Advantages

- Stable
- Authenticated
- Cross-device support
- Ideal for SaaS platforms

---

### 3. Behavioral Fingerprint

If no persistent identifier exists,

the resolver creates

```
SHA256(IP + User-Agent)
```

This provides temporary user tracking until a stronger identity becomes available.

---

### 4. UUID Generation

If none of the above identifiers exist,

the resolver generates

```
UUIDv4
```

stores it as

```
X-TrianSec-User-ID
```

and upgrades future requests into persistent identities.

This allows anonymous visitors to become consistently identifiable without requiring login.

---

## 🔄 Identity Resolution Flow

```text
Incoming Request
        │
        ▼
Extract Client IP
        │
        ▼
API Key Present?
   │            │
  Yes           No
   │            │
Validate API Key │
   │            │
Authenticated?   │
   │            │
   ▼            ▼
Resolve User   Anonymous Identity
Identifier
   │
   ▼
Cookie?
   │
 JWT?
   │
 Fingerprint?
   │
 Generate UUID
   │
   ▼
Composite Identity
(api:key:user:id)
   │
   ▼
Behavioral Fingerprint
   │
   ▼
Risk Engine
```

---

## 🎯 Why It Exists

In a B2B platform model, a single client API key multiplexes traffic from thousands of unique end-users. Without this resolver, the core system cannot distinguish between a single malicious user attacking the client's app and a high-volume traffic surge from legitimate consumers.

### 🧠 Importance in the System
* **Tenant Isolation**: Ensures one client's misconfigured software or noisy users cannot deplete shared platform resources.
* **Per-User Rate Limiting**: Enables enforcement of security rules *within* a client's global token allotment.
* **B2B Reputation Scoring**: Provides traffic intelligence metrics to show clients which of their specific endpoints or end-users exhibit malicious signatures.
* **Fraud Detection**: Identifies if a client's secret API key has been leaked or embedded directly into a public front-end codebase inappropriately.

---

## 🍪 Persistent User Tracking

For first-time users, the resolver automatically generates a secure UUID and stores it inside

```
X-TrianSec-User-ID
```

Cookie settings

| Setting | Value |
|----------|-------|
| HttpOnly | ✅ |
| Secure | ✅ |
| SameSite | Lax |
| Path | / |
| Lifetime | 1 year |

Benefits

- Stable identities
- Better reputation tracking
- Lower false positives
- Better abuse correlation
- Survives IP changes

---

## 🧠 Behavioral Fingerprint

Behavioral fingerprints are separate from user identities.

The fingerprint captures request characteristics instead of user ownership.

Authenticated fingerprint:

```
SHA256(
API_KEY +
User-Agent +
Accept-Language +
Accept-Encoding +
Path
)
```

Anonymous fingerprint:

```
SHA256(
User-Agent +
Accept-Language +
Accept-Encoding +
Path
)
```

Behavioral fingerprints are used for

- behavioral clustering
- anomaly detection
- trust scoring
- adaptive rate limiting

rather than permanent identification.

---

## 🆔 Composite Identity

Every authenticated request receives a globally unique identity.

Format

```
api:<api_key_id>:user:<user_identifier>
```

Examples

```
api:12:user:76b5...
api:12:user:john@example.com
api:12:user:f14ac...
```

This prevents collisions between tenants.

The same downstream user existing under two different API customers becomes two independent identities.

```
Tenant A
api:15:user:alice

Tenant B
api:42:user:alice
```

These identities remain completely isolated.

---
### Tenant Authentication Flow
1. Intercept the incoming payload and inspect the `X-API-KEY` header.
2. Query the storage backend or cache for the tenant matching the key.
3. Validate if the client account status is currently marked active.
4. Extract the downstream end-user network parameters and apply an isolated session tracking index.

```text
Tenant
   │
   ├── API Key
   │      │
   │      ├── User Identity
   │      │       │
   │      │       ├── Cookie
   │      │       ├── JWT
   │      │       ├── Fingerprint
   │      │       └── UUID
   │      │
   │      └── Behavioral Fingerprint
   │
   └── Composite Identity
```

---

## 🔐 Security Improvements

Compared with the previous implementation, the resolver now provides:

- API key cache support
- Persistent user identities
- Cookie-based tracking
- JWT integration
- Composite identities
- Tenant isolation
- Better behavioral fingerprints
- Reduced false positives
- Stable anonymous user tracking
- Middleware-based cookie management

---

## ❌ What's Missing (Current Gaps)

### 1. Missing Multi-Proxy Header Support
* **Problem**: The resolver assumes all upstream environments forward traffic through standard `X-Forwarded-For` protocols.
* **Impact**: Breaks downstream end-user IP tracking when client applications rely on specialized cloud layers or CDNs.
* **Solution**: Support multi-header identification priority schemas to extract true network sources reliably.
```python
proxy_headers = ["CF-Connecting-IP", "X-Real-IP", "X-Forwarded-For"]
for header in proxy_headers:
    if header in request.headers:
        end_user_ip = request.headers[header].split(",")[0].strip()
        break
```
### 2. Missing Contextual Request ID Tracking
* **Problem**: Distributed system layers process client packages without a unified processing identifier.
* **Impact**: Impossible to map step-by-step transaction logs when debugging system crashes or tenant disputes.
* **Solution**: Automatically generate or forward a unique `X-Request-ID` signature downstream.

### 3. Missing Token Expiration Policies
* **Problem**: Generated B2B client application API keys are infinitely valid by default.
* **Impact**: If a client commits their backend configuration variables to a public repository, the key remains open forever.
* **Solution**: Enforce structural expiration timestamps within the database management entity schema.

### 4. Dynamic End-User IP Migration Tracking
* **Problem**: Legitimate users shifting from Wi-Fi networks to mobile data cells change their IP and break correlation tracking.
* **Impact**: Low-and-slow abuse signatures distributed across dynamic cell networks look like unlinked user interactions.
* **Solution**: Provide integration parameters allowing clients to pass a secure local session identifier for deep correlation tracking.

### 5. Lack of IPv6 Address Normalization
* **Problem**: Different notations of the same raw IPv6 network address read as entirely distinct string values.
* **Impact**: End-user fingerprint signatures fragment if requests vary between full, uncompressed, or short notation styles.
* **Solution**: Strip zone tracking values and standardize IPv6 strings before computing hashing pipelines.

### 6. Missing Edge Real-Time Network Blocklists
* **Problem**: Known threat vectors and scanning clusters process through token identification before being rejected.
* **Impact**: Unnecessary memory usage and computation cycles are thrown away parsing traffic from known bad subnets.
* **Solution**: Match the immediate upstream server IP directly against memory blocks before execution.

### 7. Missing Audit Trail Logging
* **Problem**: Security telemetry reports do not store a permanent, immutable record of authorization state changes.
