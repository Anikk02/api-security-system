# 🧩 Feature Builder (`feature_builder.py`)

## 📌 Purpose

The Feature Builder is responsible for transforming **raw request signals and state data** into structured **behavioral features** used by the Risk Engine.

It acts as the bridge between **data collection (State Manager + Redis)** and **intelligence (Risk Engine)**.

---

## ⚙️ Role

The Feature Builder constructs a rich set of behavioral features from multiple sources:

### 🔹 Rate Features
- Requests per second (5-second window)
- Requests per minute (60-second window)

### 🔹 Endpoint Behavior
- Unique endpoints accessed (last 60 seconds)
- Endpoint entropy (randomness of access patterns)
- Top endpoint ratio (concentration on single endpoint)

### 🔹 Error Analysis
- Error count (last 60 seconds)
- Error rate (normalized against total requests)

### 🔹 Burst Detection
- Burst score (short-term vs average traffic)
- Log-scaled normalization (base 10)

### 🔹 Identity Stability
- IP change frequency (last 5 minutes)

### 🔹 User-Agent Analysis
- Bot detection (curl, wget, python, scrapy)
- Browser detection (Chrome, Safari, Edge, Mozilla)
- Suspicious UA flag (bot without browser)

### 🔹 Time-Based Features
- Request regularity (coefficient of variation)
- Time variance (normalized interval variance)
- Average request interval (mean time between requests)

### 🔹 Raw Metadata
- IP address (for downstream usage)

---

## 🧱 Output Structure

The component returns a feature dictionary:

```python
features = {
    'req_per_sec': float,
    'req_per_min': int,
    'unique_endpoints': int,
    'endpoint_entropy': float,
    'top_endpoint_ratio': float,
    'error_rate': float,
    'burst_score': float,
    'is_rate_limited': int,
    'is_burst': int,
    'is_suspicious_ua': int,
    'ip_changes': int,
    'request_regularity': float,
    'is_bot': int,
    'is_browser': int,
    'time_variance': float,
    'time_mean': float,
    'ip_address': str
}
```

---

## 🔄 Flow Integration

Signals + State Manager -> Feature Builder (this component) -> Risk Engine

---

## 🎯 Why It Exists

Raw data (requests, timestamps, logs) is not directly usable for decision-making.

This component converts raw inputs into:

- Quantifiable metrics
- Behavioral patterns
- ML-ready features

---

## 🧠 Importance in the System

This is the **feature engineering layer**, which is critical for system intelligence:

- Determines the quality of risk scoring
- Directly impacts detection accuracy
- Enables behavior-based analysis instead of static rules

Without this component:

- Risk Engine becomes ineffective
- No meaningful pattern detection
- System reduces to basic rule-based filtering

---

## ⚡ Performance Optimizations

### Redis Pipeline
- Single pipeline for all Redis reads in one round trip
- Eliminates 5+ separate Redis calls per request

### Efficient Parsing
- Type conversion helpers (to_int, to_float)
- Handles bytes, strings, and numeric types uniformly

### Debug Log Sampling
- Debug prints only for 1 percent of users (hash(user_id) mod 100 == 0)
- Prevents log spam in production

---

## 📐 Key Algorithms

### Endpoint Entropy (Normalized)

Raw entropy calculated using Shannon entropy formula, then normalized against theoretical maximum based on 50 possible endpoints.

raw_entropy = -Σ(p * log2(p))

endpoint_entropy = min(raw_entropy / log2(50), 1.0)

### Burst Score (Log-Normalized)

Compares current request rate against average rate, then compresses using log scaling.

if avg_per_sec > 0.1:
    burst_score = req_per_sec / avg_per_sec
    burst_score = log1p(burst_score) / log1p(10)
else:
    burst_score = 0.0

### Request Regularity

Uses coefficient of variation to measure consistency of request intervals.

cv = std_dev / mean_interval

regularity = 1 / (1 + cv)

### Time Variance

Measures how much intervals deviate from the average, bounded to 1.0.

normalized = interval / mean_interval

variance = Σ((normalized - 1)²) / n

time_variance = min(variance, 1.0)

---

## 🔧 Configuration Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| MAX_ENDPOINT_ENTROPY | log2(50) ≈ 5.64 | Normalization ceiling for entropy |
| BURST_BASELINE_THRESHOLD | 0.1 | Minimum req/sec for burst calculation |
| Rate limit threshold | 100 | Requests per minute to trigger is_rate_limited |
| Burst threshold | 0.6 | Burst score to trigger is_burst |
| Min timestamps for regularity | 6 | Need at least 5 intervals for calculation |

---

## ⚠️ Design Considerations

- Must be efficient (runs on every request)
- Requires fast access to Redis state
- Feature normalization is critical (entropy, burst, variance)
- Should avoid noisy or unstable features

---

## 🚀 Future Enhancements

- Geo-IP enrichment (location-based behavior)
- Device fingerprinting beyond User-Agent
- Sequence-based features (request flow patterns)
- Historical trend features (long-term behavior)
- ML feature scaling and transformation pipelines

---

## 🏁 Summary

The Feature Builder converts raw signals into **structured behavioral intelligence**, forming the foundation for accurate risk scoring and anomaly detection.