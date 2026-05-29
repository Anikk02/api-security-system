# 🧩 Feature Builder (`feature_builder.py`)

## 📌 Purpose

The Feature Builder is responsible for transforming **raw request signals and state data** into structured **behavioral features** used by the Risk Engine.

It acts as the bridge between **data collection (State Manager + Signals)** and **intelligence (Risk Engine)**.

---

## ⚙️ Role

The Feature Builder constructs a rich set of behavioral features from multiple sources:

### 🔹 Rate Features
- Requests per second
- Requests per minute

### 🔹 Endpoint Behavior
- Unique endpoints accessed
- Endpoint entropy (randomness of access patterns)

### 🔹 Error Analysis
- Error count
- Error rate (smoothed)

### 🔹 Burst Detection
- Request burst ratio (short-term vs average traffic)
- Log-scaled normalization

### 🔹 Identity Stability
- IP change frequency

### 🔹 User-Agent Analysis
- Bot detection (curl, wget, scripts)
- Browser detection

### 🔹 Time-Based Features
- Request intervals
- Request regularity (pattern consistency)
- Time variance (normalized)
- Average request interval

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

```
Signals + State Manager
        ↓
Feature Builder (this component)
        ↓
Risk Engine
```

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