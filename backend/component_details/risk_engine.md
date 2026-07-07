# 📊 Risk Engine (`risk_engine.py`)

## 📌 Purpose

The Risk Engine is responsible for computing a **risk score for each incoming request** based on behavioral patterns, request characteristics, and anomaly signals.

---

## ⚙️ Role

The Risk Engine aggregates multiple risk dimensions:

### 🔹 Behavioral Risk (40% weight)
- Requests per minute
- Burst activity patterns
- Suspicious user agents

### 🔹 Pattern Risk (35% weight)
- Endpoint entropy (random scanning detection)
- Repetition patterns (bot-like behavior)

### 🔹 Endpoint Risk (25% weight)
- Access to sensitive endpoints (e.g., `/login`, `/admin`)
- HTTP methods (POST, PUT, DELETE)

---

## 📈 Output

The engine returns:

- `risk_score` → float (0.0 to 1.0)
- `label` → low / medium / high
- `explanation` → human-readable reasoning
- `contributions` → breakdown of feature impact


---

## 🎯 Why It Exists

To convert raw behavioral and request signals into a **quantifiable and explainable risk metric**.

---

## 🧠 Importance in the System

This is the **intelligence core** of the system:

- Determines how dangerous a request is
- Drives decision-making
- Provides transparency through explanations

Without this component:

- Decisions become arbitrary
- System loses explainability
- No measurable threat assessment exists

---

## 📐 Risk Scoring Formula

The final risk score is a weighted combination of three sub-scores:

`risk = (behavior_score * 0.4) + (pattern_score * 0.35) + (endpoint_score * 0.25)`

### Behavior Score Calculation

`req_score = min(req_per_min / 60, 1.0)`

`burst_score = min(max(burst_ratio, 0.0), 1.0)`

`combined = 1 - (1 - req_score) * (1 - burst_score)`

`ua_score = 0.3 if is_suspicious_ua else 0.0`

`behavior_score = 1 - (1 - combined) * (1 - ua_score)`

### Pattern Score Calculation

`entropy = min(max(endpoint_entropy, 0.0), 1.0)`

`top_ratio = min(max(top_endpoint_ratio, 0.0), 1.0)`

`pattern_score = 1 - (1 - entropy) * (1 - top_ratio)`

### Endpoint Score Calculation
```python
if sensitive_endpoint:
      endpoint_score = 0.6
else:
      endpoint_score = 0.0

if sensitive and method in ["POST", "PUT", "DELETE"]:
      if req_rate > 20 or entropy > 0.6:
            method_score = 0.4
      elif req_rate > 10:
            method_score = 0.25
      else:
            method_score = 0.1
else:
      method_score = 0.0

endpoint_score = 1 - (1 - endpoint_score) * (1 - method_score)
```

---

## 🔧 Adaptive Thresholds

The engine uses dynamic thresholds based on recent risk scores:

- High threshold: 85th percentile of recent scores (minimum 0.70, maximum 0.90)
- Medium threshold: 65th percentile of recent scores (minimum 0.45, maximum 0.80)
- Exponential smoothing applied (alpha = 0.3)
- Requires at least 30 recent scores before adapting

---

## 📊 Example Risk Score Calculation

### Scenario 1: Malicious Bot Scanning Endpoints

**Input Features:**
- `req_per_min`: 120 requests per minute
- `burst_score`: 0.85
- `is_suspicious_ua`: True
- `endpoint_entropy`: 0.92
- `top_endpoint_ratio`: 0.15
- `endpoint`: `/api/user/123`
- `method`: `GET`
- `sensitive_endpoint`: True

**Step 1: Calculate Behavior Score**

`req_score = min(120 / 60, 1.0) = 1.0`

`burst_score = 0.85`

`combined = 1 - (1 - 1.0) * (1 - 0.85) = 1.0`

`ua_score = 0.3`

`behavior_score = 1 - (1 - 1.0) * (1 - 0.3) = 1.0`

**Step 2: Calculate Pattern Score**

`entropy = 0.92`

`top_ratio = 0.15`

`pattern_score = 1 - (1 - 0.92) * (1 - 0.15) = 1 - (0.08 * 0.85) = 1 - 0.068 = 0.932`

**Step 3: Calculate Endpoint Score**

`endpoint_score = 0.6`

`method = GET` (not POST/PUT/DELETE) so `method_score = 0.0`

`endpoint_score = 1 - (1 - 0.6) * (1 - 0.0) = 0.6`

**Step 4: Calculate Final Risk Score**

`risk = (1.0 * 0.4) + (0.932 * 0.35) + (0.6 * 0.25)`

`risk = 0.4 + 0.3262 + 0.15 = 0.8762`

**Result:** `risk_score = 0.88`, `label = "high"`

**Explanation:** "Abnormal traffic spike, Suspicious access pattern, Suspicious user agent"

---

### Scenario 2: Normal User Behavior

**Input Features:**
- `req_per_min`: 15 requests per minute
- `burst_score`: 0.1
- `is_suspicious_ua`: False
- `endpoint_entropy`: 0.25
- `top_endpoint_ratio`: 0.85
- `endpoint`: `/home`
- `method`: `GET`
- `sensitive_endpoint`: False

**Step 1: Calculate Behavior Score**

`req_score = min(15 / 60, 1.0) = 0.25`

`burst_score = 0.1`

`combined = 1 - (1 - 0.25) * (1 - 0.1) = 1 - (0.75 * 0.9) = 1 - 0.675 = 0.325`

`ua_score = 0.0`

`behavior_score = 0.325`

**Step 2: Calculate Pattern Score**

`entropy = 0.25`

`top_ratio = 0.85`

`pattern_score = 1 - (1 - 0.25) * (1 - 0.85) = 1 - (0.75 * 0.15) = 1 - 0.1125 = 0.8875`

**Step 3: Calculate Endpoint Score**

`endpoint_score = 0.0` (not sensitive)

`method_score = 0.0`

`endpoint_score = 0.0`

**Step 4: Calculate Final Risk Score**

`risk = (0.325 * 0.4) + (0.8875 * 0.35) + (0.0 * 0.25)`

`risk = 0.13 + 0.3106 + 0.0 = 0.4406`

**Result:** `risk_score = 0.44`, `label = "low"`

**Explanation:** "Normal behavior"

---

### Scenario 3: Credential Stuffing Attack

**Input Features:**
- `req_per_min`: 80 requests per minute
- `burst_score`: 0.7
- `is_suspicious_ua`: True
- `endpoint_entropy`: 0.35
- `top_endpoint_ratio`: 0.95
- `endpoint`: `/login`
- `method`: `POST`
- `sensitive_endpoint`: True

**Step 1: Calculate Behavior Score**

`req_score = min(80 / 60, 1.0) = 1.0`

`burst_score = 0.7`

`combined = 1 - (1 - 1.0) * (1 - 0.7) = 1.0`

`ua_score = 0.3`

`behavior_score = 1 - (1 - 1.0) * (1 - 0.3) = 1.0`

**Step 2: Calculate Pattern Score**

`entropy = 0.35`

`top_ratio = 0.95`

`pattern_score = 1 - (1 - 0.35) * (1 - 0.95) = 1 - (0.65 * 0.05) = 1 - 0.0325 = 0.9675`

**Step 3: Calculate Endpoint Score**

`endpoint_score = 0.6`

`method = POST` and `req_rate = 80 > 20` so `method_score = 0.4`

`endpoint_score = 1 - (1 - 0.6) * (1 - 0.4) = 1 - (0.4 * 0.6) = 1 - 0.24 = 0.76`

**Step 4: Calculate Final Risk Score**

`risk = (1.0 * 0.4) + (0.9675 * 0.35) + (0.76 * 0.25)`

`risk = 0.4 + 0.3386 + 0.19 = 0.9286`

**Result:** `risk_score = 0.93`, `label = "high"`

**Explanation:** "Abnormal traffic spike, Endpoint abuse detected, Sensitive endpoint access, Suspicious user agent"

---

## 🔧 Configuration Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| WEIGHTS['behavior'] | 0.4 | Weight for behavioral risk |
| WEIGHTS['pattern'] | 0.35 | Weight for pattern risk |
| WEIGHTS['endpoint'] | 0.25 | Weight for endpoint risk |
| Smoothing alpha | 0.3 | Exponential smoothing factor |
| Min samples for adaptation | 30 | Minimum scores before adapting |
| High threshold floor | 0.70 | Minimum high threshold |
| High threshold ceiling | 0.90 | Maximum high threshold |
| Medium threshold floor | 0.45 | Minimum medium threshold |
| Medium threshold ceiling | 0.80 | Maximum medium threshold |

### Sensitive Endpoints

**Exact matches:**
- `/login`, `/auth`, `/admin`, `/payment`, `/reset-password`, `/api/data`, `/api/secure`

**Prefix matches:**
- `/api/admin`, `/api/user`, `/api/secure`, `/api/data`

---

## ❌ What's Missing (Current Gaps)

### 1. No True ML Model
**Problem:** Current implementation uses rule-based thresholds, not trained models.

**Impact:** Cannot learn from historical attack patterns.

**Solution:** Integrate with ML framework (e.g., scikit-learn, TensorFlow).

### 2. Missing Feature Correlation
**Problem:** Features are treated independently.

**Impact:** Misses complex attack patterns that combine multiple signals.

**Solution:** Add interaction terms or use non-linear models.

### 3. No User-Specific Baselines
**Problem:** Same thresholds apply to all users.

**Impact:** High-volume legitimate users may get false positives.

**Solution:** Per-user adaptive baselines.

### 4. Missing Time-of-Day Normalization
**Problem:** Traffic patterns at 3 AM vs 3 PM treated equally.

**Impact:** Unusual hour activity not properly weighted.

**Solution:** Add time-based risk scaling.

### 5. No Sequence Detection
**Problem:** Request order is ignored.

**Impact:** Cannot detect multi-step attack sequences.

**Solution:** Add Markov chains or RNN-based sequence detection.

### 6. Missing Real-Time Feature Updates
**Problem:** Features are static per request.

**Impact:** Cannot react to rapid behavior changes within same session.

**Solution:** Stream-based feature updates.

### 7. No Confidence Scoring
**Problem:** No measure of certainty for risk scores.

**Impact:** Cannot distinguish between confident and uncertain decisions.

**Solution:** Add uncertainty estimation (e.g., Bayesian approaches).

### 8. Missing A/B Testing Framework
**Problem:** Cannot test new weights against production traffic.

**Impact:** Risky to update risk formulas.

**Solution:** Implement shadow mode with comparative logging.

### 9. No Explainability for ML
**Problem:** Rule-based explanations don't work for ML models.

**Impact:** Cannot explain ML-based decisions.

**Solution:** Add SHAP or LIME for model interpretability.

### 10. Missing Feedback Loop
**Problem:** No mechanism to learn from false positives/negatives.

**Impact:** System cannot improve over time.

**Solution:** Collect ground truth labels and retrain periodically.

---

## 🚀 Future Enhancements

- Replace rule-based scoring with trained anomaly detection models
- Add sequence-based behavior modeling (LSTM/Transformers)
- Implement per-user adaptive thresholds
- Add time-of-day and day-of-week normalization
- Integrate with ML framework for real model training
- Add SHAP/LIME for ML explainability
- Implement shadow mode for A/B testing
- Add confidence scoring for risk estimates
- Create feedback loop for continuous learning
- Add real-time feature streaming

---

## 📋 Priority Improvements

| Priority | Missing Feature | Impact |
|----------|-----------------|--------|
| High | User-specific baselines | False positives |
| High | Feedback loop | Continuous improvement |
| High | Confidence scoring | Decision quality |
| Medium | True ML model | Detection accuracy |
| Medium | Time-of-day normalization | Context awareness |
| Medium | Sequence detection | Complex attack detection |
| Low | A/B testing framework | Safe deployment |
| Low | Feature correlation | Pattern discovery |
| Low | Real-time updates | Responsiveness |

---

## ⚠️ Design Considerations

- Weight tuning is critical for accuracy
- Must remain interpretable (avoid black-box decisions)
- Current logic is rule-based (not trained ML model)
- Adaptive thresholds prevent static baselines
- Probabilistic OR fusion prevents double-counting
- Sensitive endpoint list must be maintained

---

## 🏁 Summary

The Risk Engine transforms raw input signals into **actionable intelligence**, enabling accurate, explainable, and consistent security decisions. It uses weighted scoring with three risk dimensions, adaptive thresholds based on recent traffic, and probabilistic fusion to combine signals. The engine is currently rule-based but designed to be replaced with trained ML models in the future.