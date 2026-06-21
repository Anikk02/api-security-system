# ⚙️ Analysis Pipeline (`analysis_pipeline.py`)

## 📌 Purpose

The Analysis Pipeline runs **after the HTTP response has been returned** to the client. It owns ALL heavy processing work that would otherwise block the request-response cycle.

---

## ⚙️ Role

This component performs all post-response processing:

### 🔹 Feature Building
- 5-8 Redis reads per request
- Behavioral pattern extraction

### 🔹 Risk Scoring
- Mathematical risk computation
- ML model inference
- Contribution analysis

### 🔹 Penalty Management
- Reputation reads and writes
- Block/throttle decision enforcement
- Redis state updates

### 🔹 Database Logging
- RequestLog (request metadata)
- DecisionLog (security decisions)
- FeatureLog (behavioral features)
- MLPrediction (model outputs)

### 🔹 Redis State Updates
- `user:{id}:risk_score` → fast-path for next request
- `user:{id}:blocked` → hard block enforcement
- `user:{id}:throttled` → soft throttle enforcement
- `rep:ip/user/fp` → reputation signals

---

## 🔄 Flow Integration

Client Request → Fast Path Decision → HTTP Response → Analysis Pipeline (async)

Analysis Pipeline then calls:
- Feature Builder
- Risk Engine
- Penalty Manager
- Database Logger

Results are written back to Redis for next request's fast path.

---

## 🎯 Why It Exists

To separate **fast-path decisions** (sub-5ms) from **heavy analysis** (50-200ms). This allows:

- Immediate response to client
- Comprehensive security analysis without blocking
- State updates for future requests
- Complete audit trail

Without this component:

- Request latency would be 50-200ms (unacceptable)
- Heavy processing would block response
- Cannot run ML models in real-time

---

## 🧠 Importance in the System

This is the **offline processing engine** that enables:

- **Low latency** for API responses
- **Rich analysis** without performance penalty
- **Learning over time** via state updates
- **Full observability** through logging

Without this component:

- System would be too slow for production
- No behavioral tracking
- No ML capabilities

---

## 📊 Processing Steps

### Step 1: Error Tracking
Updates error counter in Redis if status code is 400 or higher.

### Step 2: Feature Building
Calls FeatureBuilder.build() to extract behavioral features from Redis state.

Failure handling: Returns empty features dictionary if builder fails.

### Step 3: Risk Scoring
Calls compute_risk() to calculate risk score using request signals, behavioral features, and ML model if available.

Returns:
- risk_score (float 0-1)
- label_ml (model classification)
- risk_explanation (text)
- contributions (feature importance)

Failure handling: Falls back to fast_risk_score if engine fails.

### Step 4: Penalty Application
Calls apply_penalty() to determine final action: allow, throttle, or block. Uses reputation, violation count, and risk score.

Failure handling: Defaults to "allow" with fallback reason.

### Step 5: Redis State Update
Writes risk score back to Redis for next request's fast path. TTL is 300 seconds (5 minutes). If user goes quiet, score expires and they start fresh.

### Step 6: Database Logging
Logs to four separate tables:
- RequestLog - request metadata
- DecisionLog - security decision
- FeatureLog - behavioral features
- MLPrediction - ML model outputs

---

## 🔧 Singleton Pattern

The FeatureBuilder is instantiated once at module level to prevent re-instantiation per request, reduce memory overhead, and maintain consistent state.

```python
_feature_builder: FeatureBuilder | None = None

def _get_feature_builder() -> FeatureBuilder:
    global _feature_builder
    if _feature_builder is None:
        _feature_builder = FeatureBuilder(StateManager)
    return _feature_builder
```
---

## 🗄️ Database Schema

### RequestLog Table

| Column | Type | Purpose |
|--------|------|---------|
| user_id | int | User identifier |
| endpoint | str | API endpoint path |
| ip_address | str | Client IP |
| user_agent | str | Client user agent |
| status_code | int | HTTP response status |
| request_uuid | str | Unique request identifier |

### DecisionLog Table

| Column | Type | Purpose |
|--------|------|---------|
| user_id | int | User identifier |
| request_id | int | Foreign key to RequestLog |
| action | str | allow/throttle/block |
| reason | str | Human-readable reason |
| risk_score | float | Computed risk score |
| explanation | str | Summary explanation |
| explanation_json | json | Detailed explanation |
| ground_truth_label | str | Optional label for training |
| request_uuid | str | Unique request identifier |

### FeatureLog Table

| Column | Type | Purpose |
|--------|------|---------|
| user_id | int | User identifier |
| request_id | int | Foreign key to RequestLog |
| request_uuid | str | Unique request identifier |
| features | json | All behavioral features |
| behavioral_features | json | Rate and burst metrics |
| pattern_features | json | Entropy and patterns |
| identity_features | json | IP changes, bot flags |

### MLPrediction Table

| Column | Type | Purpose |
|--------|------|---------|
| user_id | int | User identifier |
| request_id | int | Foreign key to RequestLog |
| risk_score | float | Computed risk score |
| risk_label | str | ML classification |
| explanation | str | Model explanation |
| feature_contributions | json | Feature importance |
| request_uuid | str | Unique request identifier |

---

## ❌ What's Missing (Current Gaps)

### 1. No Retry Logic on DB Failure

**Problem:** Database connection failures cause lost logs.

**Impact:** Missing audit trail and training data.

**Solution:** Implement retry with exponential backoff.

### 2. Missing Batch Processing

**Problem:** Each request triggers individual DB inserts.

**Impact:** High database load under traffic spikes.

**Solution:** Batch multiple logs into single insert.

### 3. No Circuit Breaker for Dependencies

**Problem:** Feature builder or risk engine failures cascade.

**Impact:** Entire pipeline fails for that request.

**Solution:** Implement circuit breakers per component.

### 4. Missing Metrics Collection

**Problem:** No visibility into pipeline performance.

**Impact:** Cannot detect slow components or bottlenecks.

**Solution:** Track timing per step with Prometheus.

### 5. No Dead Letter Queue

**Problem:** Failed logs are permanently lost.

**Impact:** Data loss on persistent failures.

**Solution:** Send failed logs to dead letter queue for replay.

### 6. Missing Rate Limiting on Pipeline

**Problem:** Pipeline runs for every request unconditionally.

**Impact:** Resource exhaustion under high traffic.

**Solution:** Implement sampling for low-risk requests.

### 7. No Priority Queue

**Problem:** All requests processed equally.

**Impact:** High-risk requests wait behind low-risk ones.

**Solution:** Priority queue based on fast_risk_score.

### 8. Missing Health Checks

**Problem:** No monitoring of pipeline health.

**Impact:** Silent failures go unnoticed.

**Solution:** Expose health endpoint for each component.

### 9. No Backpressure Handling

**Problem:** Pipeline can accept unlimited async tasks.

**Impact:** Memory exhaustion under sustained load.

**Solution:** Limit concurrent pipeline executions.

### 10. Missing Trace Propagation

**Problem:** No correlation between logs and pipeline runs.

**Impact:** Difficult to debug request chains.

**Solution:** Propagate trace_id through all components.

---

## 🚀 Future Enhancements

- Retry logic with exponential backoff
- Batch DB inserts for high throughput
- Circuit breakers for downstream dependencies
- Prometheus metrics collection
- Dead letter queue for failed logs
- Sampling for low-risk requests
- Priority queue based on risk score
- Health check endpoints
- Backpressure with semaphore limits
- Distributed tracing integration

---

## 📋 Priority Improvements

| Priority | Missing Feature | Impact |
|----------|-----------------|--------|
| High | Batch DB inserts | Database load |
| High | Backpressure handling | Memory usage |
| High | Metrics collection | Observability |
| Medium | Retry logic | Data durability |
| Medium | Circuit breakers | Resilience |
| Medium | Sampling | Resource usage |
| Low | Dead letter queue | Data durability |
| Low | Priority queue | Latency |
| Low | Trace propagation | Debugging |

---

## ⚠️ Design Considerations

- Runs after response to avoid blocking
- All exceptions are caught and logged (failures don't crash pipeline)
- Singleton pattern for FeatureBuilder
- Separate DB session per pipeline run
- TTL-based Redis state expiration
- Feature extraction failures fall back to empty dicts

---

## 🏁 Summary

The Analysis Pipeline is the **heavy processing engine** that runs asynchronously after each request. It owns feature building, risk scoring, penalty application, Redis state updates, and database logging. This architecture enables sub-5ms fast-path decisions while still providing comprehensive security analysis and observability.