# 🚦 Request Middleware (`request_middleware.py`)

## 📌 Purpose

The Request Middleware acts as the **primary entry point** of the API security system. It intercepts every incoming request before it reaches the application's business logic and ensures that it is analyzed, evaluated, and processed according to security policies.

**Target latency: <15ms** (2 Redis GETs + 1 pipeline write).

---

## ⚙️ Role

The middleware orchestrates the entire security pipeline:

- Intercepts all incoming HTTP requests
- Resolves identity using the Identity Resolver
- Extracts request signals (IP, endpoint, method, etc.)
- **Fast-path decision** using pre-computed Redis signals (no math, no DB)
- Enforces blocking and rate limiting
- Triggers background analysis pipeline for heavy work
- Returns final response with appropriate headers

---

## 🔄 Flow Integration

Incoming Request → Request Middleware → Identity Resolver + Signals Extractor → Fast-Path Decision (Redis) → Block/Rate Limit/Throttle/Normal → Background Analysis Pipeline (after response)

**Note:** Heavy work runs AFTER the response is returned. The risk_score written by background task feeds the NEXT request's fast-path.

---

## 🎯 Why It Exists

Security must be enforced **before business logic execution**. This component ensures early threat detection, prevention of malicious requests reaching backend systems, centralized orchestration, and sub-15ms latency.

---

## 🧠 Importance in the System

This is the **core execution pipeline controller** that connects all modules, ensures consistent processing, separates fast-path from heavy analysis, and maintains system integrity.

Without this component, the system becomes fragmented and security enforcement becomes inconsistent.

---

## 🚀 Fast-Path Decision Logic

The middleware contains the **only decision logic in the hot path**. It uses pre-computed Redis signals with no math, no loops, no DB.

```python
async def _fast_decision(blocked: bool, throttled: bool, risk_score: float):
    if blocked:
        return "block", "User or IP is temporarily blocked"
    if throttled:
        return "throttle", "Rate limit active"
    if risk_score > 0.70:
        return "block", "Severe risk score detected"
    if risk_score > 0.50:
        return "throttle", "High risk detected"
    if risk_score > 0.45:
        return "throttle", "Suspicious activity detected"
    return "allow", "Normal traffic"
```
---

## Fast-Path Decision Matrix

| Condition | Action | Reason |
|-----------|--------|--------|
| blocked = True | block | User or IP is temporarily blocked |
| throttled = True | throttle | Rate limit active |
| risk_score > 0.70 | block | Severe risk score detected |
| risk_score > 0.50 | throttle | High risk detected |
| risk_score > 0.45 | throttle | Suspicious activity detected |
| else | allow | Normal traffic |

---

## 📊 Processing Steps

**Step 0: Safe Endpoint Bypass**
Endpoints starting with `/api/dashboard` or `/health` bypass all security checks.

**Step 1: Identity Resolution**
Calls `resolve_identity()` to get user_id, ip_address, and behavioral fingerprint.

**Step 2: Signal Extraction**
Calls `extract_signals()` to get endpoint, method, user_agent, etc.

**Step 3: Fast-Path Decision**
Single Redis pipeline call to `get_decision_signals()` returns blocked, risk_score, and throttled status.

**Step 4: Request Tracking (Fire-and-Forget)**
Async task calls `track_request_async()` to update Redis with timestamp, endpoint, and IP.

**Step 5: Block Fast Path**
If action is "block", returns 429 immediately with background analysis task.

**Step 6: Rate Limiting Check**
Two rate limiters based on risk_score: strict_limiter (30 req/min) for risk_score > 0.6, minute_limiter (60 req/min) for risk_score <= 0.6.

**Step 7: Throttled Flag Handling**
If throttled flag is active, processes request but adds throttle headers.

**Step 8: Normal Flow**
Processes request, adds headers, triggers background analysis.

**Step 9: Background Analysis**
`asyncio.ensure_future(run_analysis_pipeline(...))` runs after response is sent.

---

## 🔧 Rate Limiters

| Limiter | Max Requests | Window | Trigger |
|---------|--------------|--------|---------|
| minute_limiter | 60 | 60 seconds | risk_score <= 0.6 |
| strict_limiter | 30 | 60 seconds | risk_score > 0.6 |

### Rate Limit Response Headers

| Header | Value |
|--------|-------|
| Retry-After | seconds until reset |
| X-RateLimit-Limit | max requests per window |
| X-RateLimit-Remaining | 0 |
| X-RateLimit-Reset | timestamp of reset |

---

## 📋 Response Headers Added

| Header | Purpose |
|--------|---------|
| X-Request-UUID | Unique request identifier for tracing |
| X-Process-Time | Processing time in seconds |
| X-RateLimit-Limit | Rate limit max (when throttled) |
| X-RateLimit-Remaining | Remaining requests (when throttled) |
| X-RateLimit-Reset | Reset timestamp (when throttled) |
| X-Throttled | "true" when throttle flag active |
| Retry-After | Seconds to wait (block/rate limit) |

---

## ❌ What's Missing (Current Gaps)

### 1. No Circuit Breaker for Redis
**Problem:** Redis failures cause middleware to fail.
**Impact:** Complete system outage.
**Solution:** Implement circuit breaker with fallback to allow mode.

### 2. No Request Sampling for Low-Risk Traffic
**Problem:** Every request triggers background analysis.
**Impact:** Resource exhaustion under high traffic.
**Solution:** Sample low-risk requests (e.g., 10% of allow decisions).

### 3. Missing Distributed Tracing
**Problem:** No OpenTelemetry integration.
**Impact:** Difficult to debug request chains.
**Solution:** Add trace_id propagation and spans.

### 4. No Backpressure Handling
**Problem:** Unlimited async tasks can be created.
**Impact:** Memory exhaustion under sustained load.
**Solution:** Limit concurrent background tasks with semaphore.

### 5. Missing Graceful Degradation
**Problem:** No fallback when Redis is slow.
**Impact:** Request latency spikes.
**Solution:** Timeout with fallback to allow mode.

### 6. No Health Check Endpoint for Middleware
**Problem:** Cannot monitor middleware health independently.
**Impact:** Silent failures go unnoticed.
**Solution:** Expose `/health/middleware` endpoint.

### 7. Missing Request Size Limits
**Problem:** No protection against large request bodies.
**Impact:** DoS attacks via memory exhaustion.
**Solution:** Add configurable request size limits.

### 8. No IP Reputation Check Before Identity Resolution
**Problem:** Known malicious IPs still go through identity resolution.
**Impact:** Wasted resources.
**Solution:** Check IP blocklist before identity resolution.

### 9. Missing Rate Limit Headers on Normal Responses
**Problem:** Clients don't know their remaining quota.
**Impact:** Poor client experience.
**Solution:** Add rate limit headers to all responses.

### 10. No Request Deduplication
**Problem:** Duplicate requests are processed identically.
**Impact:** Wasted resources on retries.
**Solution:** Short-term deduplication cache.

---

## 🚀 Future Enhancements

- Circuit breaker for Redis failures
- Request sampling for low-risk traffic
- OpenTelemetry distributed tracing
- Backpressure with semaphore limits
- Graceful degradation on Redis timeouts
- Health check endpoints
- Request size limits
- IP blocklist check before identity resolution
- Rate limit headers on all responses
- Request deduplication cache

---

## 📋 Priority Improvements

| Priority | Missing Feature | Impact |
|----------|-----------------|--------|
| High | Circuit breaker for Redis | Availability |
| High | Backpressure handling | Memory usage |
| High | Request sampling | Resource usage |
| Medium | Distributed tracing | Debugging |
| Medium | Graceful degradation | Reliability |
| Medium | Health checks | Monitoring |
| Low | Request size limits | Security |
| Low | IP blocklist pre-check | Efficiency |
| Low | Rate limit headers | Client experience |

---

## ⚠️ Design Considerations

- Must be highly performant (target <15ms)
- Fully asynchronous to avoid blocking
- Must handle failures gracefully (fallback decisions)
- Should minimize latency overhead
- Heavy work delegated to background pipeline
- Fast-path uses only pre-computed Redis signals
- Safe endpoints bypass all security checks

---

## 🏁 Summary

The Request Middleware serves as the **central orchestration layer**, ensuring that every request is analyzed, evaluated, and enforced with security policies in real time. It uses a fast-path decision model with pre-computed Redis signals to achieve sub-15ms latency, while delegating heavy processing to a background analysis pipeline. The middleware handles blocking, rate limiting, throttle flags, and normal flow, always returning appropriate headers for observability.