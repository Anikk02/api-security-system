# 🧠 State Manager (`state_manager.py`)

## 📌 Purpose

The State Manager provides **real-time behavioral state management** using Redis. It acts as the short-term memory layer for the entire security system.

---

## ⚙️ Role

### 🔹 Fast Decision Path
- Single Redis pipeline for decision signals
- Checks block status (user, IP, fingerprint)
- Retrieves cached risk score
- Checks throttle status

### 🔹 Request Tracking
- Tracks request timestamps (sliding windows)
- Tracks endpoints accessed per user
- Tracks IP addresses per user
- Tracks error counts

### 🔹 Rate Limiting
- ZSET-based sliding window implementation
- Configurable window size (default 60 seconds)
- Configurable max requests (default 100)

### 🔹 Block Management
- User blocking with TTL (max 12 hours)
- IP blocking with TTL
- Fingerprint blocking with TTL

### 🔹 Violation Tracking
- Increments violation counter
- 30-minute expiration window

### 🔹 Feature Building Support
- Get recent endpoints by time window
- Get request timestamps for regularity analysis
- Get IP change count

---

## 🔄 Flow Integration
```text
Middleware / Risk Engine / Penalty Manager / Feature Builder
↓
State Manager (this component)
↓
Redis
```
---

---

## 🎯 Why It Exists

Behavioral security requires **low-latency state tracking** (sub-millisecond), which traditional databases cannot provide. Redis enables real-time sliding windows, counters, and block checks.

---

## 🧠 Importance in the System

Acts as the **short-term memory** for the entire system:

- Enables real-time decisions (sub-5ms fast path)
- Supports sliding window calculations
- Powers anomaly detection
- Stores reputation scores
- Maintains block state

Without this component:

- No rate limiting
- No behavioral tracking
- No block state persistence
- System becomes stateless and ineffective

---

## 📊 Redis Data Structures

| Key Pattern | Type | TTL | Purpose |
|-------------|------|-----|---------|
| `user:{id}:timestamps` | Sorted Set | 300s | Request timestamps for rate/regularity |
| `user:{id}:endpoints` | Sorted Set | 300s | Endpoint access patterns |
| `user:{id}:ips` | Set | 300s | IP addresses used by user |
| `user:{id}:errors` | String | 60s | Error count for current window |
| `user:{id}:violations` | String | 1800s | Violation count (30 min) |
| `user:{id}:blocked` | String | 2-12h | User block flag |
| `user:{id}:throttled` | String | 60s | Throttle flag |
| `user:{id}:risk_score` | String | 300s | Cached risk score for fast path |
| `ip:{ip}:blocked` | String | 2-12h | IP block flag |
| `fp:{fp}:blocked` | String | 2-12h | Fingerprint block flag |
| `rep:ip:{ip}` | String | 3600s | IP reputation score |
| `rep:user:{id}` | String | 3600s | User reputation score |
| `rep:fp:{fp}` | String | 3600s | Fingerprint reputation score |

---

## 🔧 Key Methods

### Fast Decision Path

`get_decision_signals(user_id, ip, fingerprint)`
- Single pipeline with 3-6 Redis commands
- Returns: (blocked, risk_score, throttled)
- Risk score boosted by fingerprint reputation (20% weight)

### Request Tracking

`track_request_async(user_id, endpoint, ip, status_code)`
- Updates timestamps ZSET
- Updates endpoints ZSET
- Tracks IP in set
- Increments error counter if status >= 400
- All operations in single pipeline

### Rate Limiting

`get_request_count(user_id, window)`
- Uses ZSET with time-based scoring
- Automatically cleans old entries

`is_rate_limited(user_id)`
- Checks if request count exceeds MAX_REQUESTS (default 100)

### Block Management

`block_user(user_id, duration)`
- Max TTL cap: 12 hours
- Sets block flag in Redis

`block_ip(ip, duration)`
- IP-level blocking

`block_fingerprint(fingerprint, duration)`
- Fingerprint-level blocking

`is_blocked(user_id)`
- Checks user block status

### Error Tracking

`increment_error(user_id)`
- Increments error counter
- Sets TTL to WINDOW_SIZE (60 seconds)

`get_error_count(user_id, window)`
- Retrieves error count

### Violation Tracking

`increment_violation(user_id)`
- Increments violation counter
- Sets TTL to 1800 seconds (30 minutes)

`get_violations(user_id)`
- Retrieves current violation count

### Feature Building Support

`get_recent_endpoints(user_id, window)`
- Returns list of endpoints accessed in time window
- Parses timestamp|endpoint format

`get_request_timestamps(user_id, window)`
- Returns list of timestamps for regularity analysis

`get_ip_change_count(user_id, window)`
- Returns number of unique IPs used

---

## ⚡ Performance Optimizations

### Pipeline Usage
All multi-step operations use Redis pipelines:
- `get_decision_signals` - 3-6 commands in one round trip
- `track_request_async` - 6-8 commands in one round trip

### Safe Redis Calls
`safe_redis_call` wrapper prevents crashes on Redis failures

### TTL-Based Cleanup
No manual cleanup needed - Redis expires keys automatically

### Max Block Duration Cap
12-hour cap prevents permanent blocks from consuming memory

---

## ❌ What's Missing (Current Gaps)

### 1. No Redis Cluster Support
**Problem:** Single Redis instance becomes bottleneck.

**Impact:** Cannot scale horizontally.

**Solution:** Implement Redis Cluster or Redis Sentinel.

### 2. Missing Connection Pool
**Problem:** Each call creates new connection overhead.

**Impact:** Increased latency under load.

**Solution:** Implement connection pooling.

### 3. No Fallback on Redis Failure
**Problem:** System crashes when Redis is unavailable.

**Impact:** Complete system failure.

**Solution:** Local memory cache fallback.

### 4. Missing Batch Operations for Feature Builder
**Problem:** Feature builder still makes multiple pipeline calls.

**Impact:** Suboptimal performance.

**Solution:** Consolidate all feature builder reads into single pipeline.

### 5. No Data Versioning
**Problem:** Cannot rollback state changes.

**Impact:** Difficult to debug state issues.

**Solution:** Add version stamps to keys.

### 6. Missing Atomic Operations
**Problem:** Some operations are not atomic.

**Impact:** Race conditions under high concurrency.

**Solution:** Use Lua scripts for complex operations.

### 7. No Key Prefix Namespacing
**Problem:** Keys are flat without environment separation.

**Impact:** Cannot run dev/staging/prod on same Redis.

**Solution:** Add environment prefix to all keys.

### 8. Missing Metrics Collection
**Problem:** No visibility into Redis performance.

**Impact:** Cannot detect slow operations.

**Solution:** Track command timing with Prometheus.

### 9. No Key Eviction Strategy
**Problem:** Depends on Redis default eviction.

**Impact:** Potential data loss under memory pressure.

**Solution:** Configure explicit maxmemory-policy.

### 10. Missing Health Checks
**Problem:** No monitoring of Redis connectivity.

**Impact:** Silent failures go unnoticed.

**Solution:** Expose Redis health endpoint.

---

## 🚀 Future Enhancements

- Redis Cluster or Sentinel for high availability
- Connection pooling for reduced latency
- Local memory fallback on Redis failure
- Batch operations for feature builder
- Lua scripts for atomic complex operations
- Environment key prefixing (dev/staging/prod)
- Prometheus metrics for Redis operations
- Configurable eviction policies
- Health check endpoints
- Data versioning for debugging

---

## 📋 Priority Improvements

| Priority | Missing Feature | Impact |
|----------|-----------------|--------|
| High | Redis Cluster/Sentinel | Availability |
| High | Connection pooling | Latency |
| High | Fallback on Redis failure | Reliability |
| Medium | Environment namespacing | Multi-tenancy |
| Medium | Health checks | Monitoring |
| Medium | Metrics collection | Observability |
| Low | Lua scripts | Consistency |
| Low | Data versioning | Debugging |
| Low | Eviction strategy | Memory management |

---

## ⚠️ Design Considerations

- Redis dependency is critical (single point of failure)
- TTL-based cleanup prevents unbounded growth
- Max block duration of 12 hours prevents memory bloat
- Pipeline usage minimizes round trips
- Safe Redis calls prevent crashes
- Risk score boosted by fingerprint reputation (20%)

---

## 🏁 Summary

The State Manager provides **fast, real-time behavioral data**, enabling intelligent and timely decisions. It uses Redis pipelines for performance, TTL-based cleanup for maintenance, and supports block management, rate limiting, and feature building. However, it lacks high availability features, connection pooling, and fallback mechanisms needed for production scale.