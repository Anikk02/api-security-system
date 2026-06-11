# Reduce Blocked / Throttled Latency to ~15ms

## Root Cause Analysis

The allowed path costs **~15ms** because it does:
```
resolve_identity  →  extract_signals  →  get_decision_signals (1 Redis pipeline)
→  track_request_async (fire-and-forget)  →  call_next  →  return
```

The blocked/throttled paths cost **200–500ms** because they do **exactly the same work** as the allowed path — resolve identity, extract signals, get decision signals — and then on top of that:

1. **Blocked path**: fires `run_analysis_pipeline` as `ensure_future` **before** `return`.  
   `ensure_future` schedules the coroutine but because of how Python asyncio works inside Starlette's `BaseHTTPMiddleware`, it can delay the response until the event loop yields. Additionally, `extract_signals` is called even though blocked requests never reach the client's business logic.

2. **Throttled path** ← **the real culprit**: it calls `await call_next(request)` which **actually executes the full client handler** (database queries, business logic, etc.) before returning. Throttled users are let through to your app, so they pay the full application latency on top of the middleware overhead.

### Latency Breakdown

| Path | Identity | Signals | Redis | Rate Limiter | App handler | Total |
|---|---|---|---|---|---|---|
| Allowed | ✅ | ✅ | ✅ 1 pipeline | ✅ 1 pipeline | ✅ ~10ms | **~15ms** |
| **Blocked** | ✅ | ✅ | ✅ 1 pipeline | ✅ 1 pipeline | ❌ skipped | **~30-50ms** (same as allowed minus app) — *actually fast already* |
| **Throttled** | ✅ | ✅ | ✅ 1 pipeline | ✅ 1 pipeline | ✅ **full app** | **200–500ms** |

> [!IMPORTANT]
> The throttled path is expensive **because throttled users ARE allowed through to the app** (`call_next` is called). Throttled ≠ blocked. This is a behavioral design decision. See **Open Questions** below.

---

## Open Questions

> [!IMPORTANT]
> **Q1: What should throttled users actually experience?**
>
> Currently, when `throttled=True` from the penalty_manager flag, the code calls `await call_next(request)` — meaning the user reaches your actual backend routes. The response is returned with throttle headers, but the handler ran.
>
> Two options:
> - **Option A (current)**: Throttled users get through to the app — response latency is dominated by the app handler (~200ms). The middleware itself is not the bottleneck here.
> - **Option B (recommended)**: Throttled users are intercepted at the middleware and get a synthetic `429` response (like blocked users) — no `call_next`, so they get ~15ms response time. Background analysis still runs. This matches your stated goal: *"throttled users are not allowed to enter client's business logic"*.
>
> **Which do you want?**

> [!NOTE]
> **Q2: Why is blocked path also slow (200–500ms)?**
>
> If blocked users already skip `call_next`, they should be ~15–30ms. If you're seeing 200–500ms on blocked too, the likely cause is `resolve_identity` — if `X-API-KEY` is present, a PostgreSQL query runs. For a bot hammering with a known key, this is a live DB query on every single request.
>
> **Option**: Move the block check to *before* identity resolution — just check `ip:{ip}:blocked` using the raw request IP, before `resolve_identity` opens any DB session.

---

## Proposed Changes

### Option B selected (recommended)

#### [MODIFY] [request_middleware.py](file:///c:/edb/api_security_system/backend/app/middleware/request_middleware.py)

**Change 1 — Early IP block check before identity resolution**

```python
# NEW: read client IP from headers before calling resolve_identity
# Check ip:{ip}:blocked in Redis BEFORE opening any DB session
raw_ip = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
         or request.client.host

ip_blocked = await redis_client.exists(f"ip:{raw_ip}:blocked")
if ip_blocked:
    # fire-and-forget background, return 429 immediately
    ...
```
This saves the entire `resolve_identity` cost (0–5ms normally, **50–200ms when DB is involved**) for known-bad IPs.

**Change 2 — Throttled users return 429, skip `call_next`**

```python
# BEFORE (throttled users go to the app):
if throttled:
    response = await call_next(request)   # ← 200–500ms app latency
    ...

# AFTER (throttled users get synthetic 429, never touch the app):
if throttled:
    asyncio.ensure_future(run_analysis_pipeline(...))
    return JSONResponse(status_code=429, ...)   # ← ~0ms
```

**Change 3 — Parallelise `resolve_identity` + `extract_signals`**

Both are currently sequential but are completely independent. Running them concurrently with `asyncio.gather` shaves their combined time by whichever is slower.

```python
# BEFORE (sequential):
identity = await resolve_identity(request)
signals  = await extract_signals(request)

# AFTER (parallel):
identity, signals = await asyncio.gather(
    resolve_identity(request),
    extract_signals(request),
)
```

---

## Verification Plan

### Manual Verification
- Simulate a blocked user → measure response time in logs (`X-Process-Time` header).
- Simulate a throttled user → verify they receive `429`, never reach the route handler, and `run_analysis_pipeline` still fires.
- Simulate a normal user → verify they still get through to the app.
- Check dashboard: reputation/risk scores still update for blocked/throttled users (background pipeline still fires).

### Expected Results
| Path | Before | After |
|---|---|---|
| Allowed | ~15ms | ~12ms (parallelised identity+signals) |
| Blocked (IP known) | 200–500ms | **~5ms** (pre-identity IP check) |
| Blocked (user) | ~30–50ms | ~15ms (same fast path) |
| Throttled | 200–500ms | **~15ms** (no `call_next`) |
