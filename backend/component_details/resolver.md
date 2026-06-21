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

```python
class ClientTenantIdentity:
    tenant_id: int              # Database internal ID of the B2B client application
    api_key: str | None         # Original API key (or masked identifier token)
    is_active: bool             # Global active/suspended flag for the client account
    
    # End-User tracking attributes (scoped tightly inside this specific tenant)
    end_user_ip: str | None     # True remote device network address of the client's user
    behavioral_fingerprint: str # Isolated unique fingerprint for this specific user session
```

### 🔄 Flow Integration

```text
End-User Device
      ↓
Client Application Integration
      ↓
  API Gateway (X-API-KEY)
      ↓
Identity Resolver (This Component: Maps Tenant + Fingerprints End-User)
      ↓
Tenant-Aware Rate Limiting & Threat Processing
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

## 🔧 Implementation Details

### Edge IP Extraction (End-User vs Proxy Chain)
```python
TRUST_PROXY = True  # Configurable

def extract_client_ips(request: Request) -> tuple[str, str]:
    # Direct network caller is typically the Client Application Server
    client_app_server_ip = request.client.host 
    
    if TRUST_PROXY:
        forwarded_ips = request.headers.get("X-Forwarded-For")
        if forwarded_ips:
            # First entry in the chain represents the original End-User device
            end_user_ip = forwarded_ips.split(",")[0].strip()
            return end_user_ip, client_app_server_ip
            
    return client_app_server_ip, client_app_server_ip
```

### Tenant Authentication Flow
1. Intercept the incoming payload and inspect the `X-API-KEY` header.
2. Query the storage backend or cache for the tenant matching the key.
3. Validate if the client account status is currently marked active.
4. Extract the downstream end-user network parameters and apply an isolated session tracking index.

### Tenant-Scoped End-User Fingerprint Generation
```python
def _generate_tenant_user_fingerprint(request: Request, tenant_id: int, end_user_ip: str) -> str:
    ua = request.headers.get("user-agent", "")
    accept_lang = request.headers.get("accept-language", "")
    accept_enc = request.headers.get("accept-encoding", "")
    
    # Fingerprint is explicitly prefixed with the Tenant ID.
    # This intentionally prevents tracking users across separate client systems.
    raw_payload = f"tenant:{tenant_id}:ip:{end_user_ip}:ua:{ua}:lang:{accept_lang}:enc:{accept_enc}"
    return hashlib.sha256(raw_payload.encode()).hexdigest()
```

---

## 📊 Logging

The resolver tracks tenant validation metrics and downstream anomalies:
* **INFO**: Tenant authentication success, dynamic end-user fingerprint generation maps.
* **WARNING**: Inactive/Suspended client key attempts, high end-user-to-IP concentration clusters.
* **DEBUG**: Complete header chain parse details, execution latency intervals.

```text
[IDENTITY] Resolving for route=/v1/sync tenant_header=present
[IDENTITY] Client App Gateway connected from ip=54.210.43.12
[IDENTITY] X-Forwarded-For end-user trace detected → user_ip=192.168.1.100
[IDENTITY] Authenticated Tenant ID=1048 [Active] User Fingerprint=e3b0c442...
```

---

## ❌ What's Missing (Current Gaps)

### 1. API Key Caching
* **Problem**: Every single downstream end-user request triggers a database query to validate the host client's API key.
* **Impact**: Extreme database connection overhead and latency spikes under real-world multi-tenant traffic.
* **Solution**: Cache verified client tenant metadata records inside a fast Redis layer with an explicit TTL.
```python
cached_tenant = await redis.get(f"tenant_key:{api_key}")
if cached_tenant:
    return ClientTenantIdentity(**json.loads(cached_tenant))
```

### 2. Rate Limiting on Invalid API Keys
* **Problem**: Zero systemic verification limits for missing, bad, or random key lookups.
* **Impact**: Attackers can run distributed brute-force token scanners directly against the primary gateway cache/database.
* **Solution**: Track consecutive auth failures based on the direct incoming client server IP address via Redis sliding blocks.
```python
failed_attempts = await redis.incr(f"failed_auth:{connecting_ip}")
if failed_attempts > 20:
    return HTTP_429_TOO_MANY_REQUESTS
```

### 3. Missing Multi-Proxy Header Support
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

### 4. No Live API Key Revocation Checking
* **Problem**: Revoking compromised client credentials manually has an propagation lag across active memory caches.
* **Impact**: Compromised tokens or banned tenants continue processing traffic until historical caches cycle naturally.
* **Solution**: Implement transactional database webhooks to clear precise key indices in Redis instantly upon deletion.

### 5. Missing Contextual Request ID Tracking
* **Problem**: Distributed system layers process client packages without a unified processing identifier.
* **Impact**: Impossible to map step-by-step transaction logs when debugging system crashes or tenant disputes.
* **Solution**: Automatically generate or forward a unique `X-Request-ID` signature downstream.

### 6. Missing Token Expiration Policies
* **Problem**: Generated B2B client application API keys are infinitely valid by default.
* **Impact**: If a client commits their backend configuration variables to a public repository, the key remains open forever.
* **Solution**: Enforce structural expiration timestamps within the database management entity schema.

### 7. Weak Anonymous End-User Fingerprinting
* **Problem**: End-users browsing under shared networks (e.g., enterprise VPNs, offices, cellular CGNAT) resolve to matching profiles.
* **Impact**: High risk of false-positives where blocking one abusive user mistakenly locks out an entire office pool on that client's app.
* **Solution**: Mix explicit system user IDs, device markers, and network context values into the hashing sequence.

### 8. Dynamic End-User IP Migration Tracking
* **Problem**: Legitimate users shifting from Wi-Fi networks to mobile data cells change their IP and break correlation tracking.
* **Impact**: Low-and-slow abuse signatures distributed across dynamic cell networks look like unlinked user interactions.
* **Solution**: Provide integration parameters allowing clients to pass a secure local session identifier for deep correlation tracking.

### 9. Lack of IPv6 Address Normalization
* **Problem**: Different notations of the same raw IPv6 network address read as entirely distinct string values.
* **Impact**: End-user fingerprint signatures fragment if requests vary between full, uncompressed, or short notation styles.
* **Solution**: Strip zone tracking values and standardize IPv6 strings before computing hashing pipelines.

### 10. Missing Edge Real-Time Network Blocklists
* **Problem**: Known threat vectors and scanning clusters process through token identification before being rejected.
* **Impact**: Unnecessary memory usage and computation cycles are thrown away parsing traffic from known bad subnets.
* **Solution**: Match the immediate upstream server IP directly against memory blocks before execution.

### 11. Missing Audit Trail Logging
* **Problem**: Security telemetry reports do not store a permanent, immutable record of authorization state changes.
