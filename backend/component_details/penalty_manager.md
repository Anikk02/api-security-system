# 🔥 Penalty Manager (`penalty_manager.py`)

## 📌 Purpose

The Penalty Manager applies **final enforcement actions** based on adjusted risk and reputation, ensuring adaptive and evolving security responses.

---

## ⚙️ Role

### 🔹 Reputation System
Maintains reputation scores for:
- IP address
- User identity
- Device fingerprint

### 🔹 Risk Adjustment
Enhances base risk using:
- Reputation scores (10% weight)
- Violation count (up to 8% boost)
- Request count (up to 5% boost)
- Error count (up to 7% boost)

Formula: adjusted_risk = min(
risk_score * 0.7
combined_rep * 0.10
min(violation_count / 20, 0.08)
min(req_count / 200, 0.05)
min(error_count / 100, 0.07),
1.0
)

---

### 🔹 Time Windows
| Window | Duration | Purpose |
|--------|----------|---------|
| Short | 60 seconds | Request count |
| Medium | 300 seconds (5 min) | Error tracking |
| Long | 1800 seconds (30 min) | Data retention |

### 🔹 Block Durations
| Severity | Duration | Use Case |
|----------|----------|----------|
| Soft | 2 hours | First offense |
| Medium | 6 hours | Repeated violations |
| Hard | 12 hours | Severe malicious activity |

### 🔹 Escalation Logic
| Adjusted Risk | Action | Condition |
|---------------|--------|-----------|
| > 0.85 | Block | Hard block with explanation |
| > 0.7 with violations > 3 | Block | Medium block |
| > 0.7 | Throttle | High risk without enough violations |
| > 0.5 | Throttle | Suspicious activity |
| <= 0.5 | Allow | Normal traffic |

### 🔹 Special Hard Rules
- Reputation > 0.9 → Immediate hard block
- IP already blocked → Fast reject
- Fingerprint already blocked → Fast reject

---

## 📈 Output

Returns:
- `final_action` → allow / throttle / block
- `reason` → explanation for enforcement
- `metadata` → adjusted risk and reputation

```Example output: ("block", "Severe malicious activity detected (risk score 92%, 7 violations, 150 requests/min)", {"adjusted_risk": 0.92, "reputation": 0.85})
```

---

## 🔄 Flow Integration

Decision Engine (Risk Score) → Penalty Manager (this component) → Redis State Updates → Final Action + Explanation

---

## 🎯 Why It Exists

To implement **adaptive enforcement**, allowing the system to evolve based on user behavior and history rather than static rules.

---

## 🧠 Importance in the System

This is the **final authority** of the system:

- Controls real enforcement decisions
- Applies long-term behavioral learning
- Enables progressive security responses
- Provides user-friendly explanations for actions

Without this component:
- System becomes static
- No adaptation to repeated behavior
- Security becomes less effective over time
- Users have no understanding of why actions were taken

---

## ⚡ Performance Optimizations

### Single Pipeline for Reads
All Redis reads happen in ONE pipeline:
- Request count (short window)
- Error count
- Violation count
- Three reputation keys (IP, user, fingerprint)
- Blocked status checks (IP, fingerprint)

### Fire-and-Forget Writes
All Redis updates run asynchronously in background task:
- Reputation score updates
- Request timestamp addition
- Block/throttle flag setting
- Risk score storage

This prevents blocking the main request thread.

---

## 📐 Key Algorithms

### Reputation Combination
`combined_rep = min(1.0, (ip_rep * 0.5 + user_rep * 0.3 + fp_rep * 0.2))`

- IP reputation: 50% weight (most volatile)
- User reputation: 30% weight (stable identity)
- Fingerprint reputation: 20% weight (device-based)

### Reputation Delta
| Action | Delta | Effect |
|--------|-------|--------|
| Block | +0.2 | Large increase |
| Throttle | +0.05 | Small increase |
| Allow | -0.02 | Decay over time |

### Fingerprint Generation
`_generate_fingerprint(ip, ua)` combines IP and User-Agent using SHA256 for device-level tracking.

---

## 🔧 Detailed Action Logic

### Hard Block (Risk > 0.85)
Triggers when adjusted risk exceeds 85% with contributing factors:
- Original risk > 80%
- More than 5 violations
- Over 100 requests per minute

Returns block with "hard" severity (12 hour duration).

### Medium Block (Risk > 0.7 AND violations > 3)
Triggers for repeated suspicious behavior with at least 3 violations in 30 minutes.
Returns block with "medium" severity (6 hour duration).

### Throttle (Risk > 0.7)
Triggers for high risk without enough violations or with:
- Risk spike > 65%
- More than 10 errors

Sets throttle flag for 60 seconds.

### Throttle (Risk > 0.5)
Triggers for suspicious activity with:
- Elevated risk > 55%
- High volume > 50 requests/min

### Allow (Risk <= 0.5)
Normal traffic with reputation decay of -0.02.

---

## 📊 Redis Keys Used

| Key Pattern | Type | TTL | Purpose |
|-------------|------|-----|---------|
| user:{user_id}:timestamps | Sorted Set | 30 min | Request timestamps |
| user:{user_id}:errors | String | - | Error count |
| user:{user_id}:violations | String | - | Violation count |
| user:{user_id}:blocked | String | 2-12 hours | Block flag |
| user:{user_id}:throttled | String | 60 sec | Throttle flag |
| user:{user_id}:risk_score | String | 5 min | Last risk score |
| rep:ip:{ip} | String | 1 hour | IP reputation |
| rep:user:{user_id} | String | 1 hour | User reputation |
| rep:fp:{fingerprint} | String | 1 hour | Fingerprint reputation |
| ip:{ip}:blocked | String | 2-12 hours | IP block flag |
| fp:{fingerprint}:blocked | String | 2-12 hours | Fingerprint block flag |

---

## ❌ What's Missing (Current Gaps)

### 1. Reputation Decay Over Time
Problem: Reputation only decays when user makes allow actions. Inactive users retain high reputation indefinitely.

Impact: Old malicious reputation never clears naturally.

Solution: Implement time-based decay job that reduces reputation by 1% per hour.

### 2. No Whitelist Support
Problem: Trusted IPs or users cannot bypass enforcement.

Impact: False positives affect known good actors.

Solution: Add whitelist check before penalty application.

### 3. Missing Rate Limit on Actions
Problem: No protection against rapid action state changes.

Impact: Could be exploited to toggle throttle/block repeatedly.

Solution: Add cooldown on state transitions.

### 4. No Persistent Storage
Problem: All reputation and violation data lives in Redis only.

Impact: Data loss on Redis restart.

Solution: Periodically sync to PostgreSQL.

### 5. Missing Webhook Notifications
Problem: No external notification when users get blocked.

Impact: Security teams cannot respond in real time.

Solution: Send webhooks on block events.

### 6. No Block Escalation
Problem: Repeated offenses after block expiration start fresh.

Impact: Persistent attackers face same short block durations.

Solution: Track block history and escalate durations.

### 7. Missing Geographic Reputation
Problem: All IPs treated equally regardless of origin.

Impact: High-risk countries not weighted appropriately.

Solution: Add GeoIP lookup and country reputation scoring.

### 8. No Time-of-Day Sensitivity
Problem: Traffic patterns at 3 AM vs 3 PM treated the same.

Impact: Unusual hour activity not flagged.

Solution: Add time-based risk factors.

### 9. Missing Audit Trail
Problem: No permanent log of when users were blocked/unblocked.

Impact: Difficult to audit enforcement actions.

Solution: Log all state changes to database.

### 10. Hardcoded Thresholds
Problem: All risk thresholds are hardcoded numbers.

Impact: Cannot tune per tenant or use case.

Solution: Make thresholds configurable via settings.

---

## 🚀 Future Enhancements

- Feedback-based learning (manual actions influence reputation)
- Per-client policy customization
- ML-driven reputation scoring
- Cross-client threat intelligence sharing
- Block escalation (longer durations for repeat offenders)
- Webhook notifications on security events
- Persistent storage with PostgreSQL sync
- Geographic reputation scoring
- Time-based risk factors
- Configurable thresholds per tenant

---

## 📋 Priority Improvements

| Priority | Missing Feature | Impact |
|----------|-----------------|--------|
| High | Persistent storage | Data durability |
| High | Whitelist support | User experience |
| High | Configurable thresholds | Flexibility |
| Medium | Block escalation | Effectiveness |
| Medium | Webhook notifications | Alerting |
| Low | Geographic reputation | Accuracy |
| Low | Time-of-day sensitivity | Detection |
| Low | Audit trail | Compliance |

---

## ⚠️ Design Considerations

- Reputation must decay to avoid permanent bias
- Blocking durations must be carefully tuned
- Must minimize false positives
- Fast-path rejection for already blocked entities
- Fire-and-forget writes prevent request blocking
- User-friendly explanations improve transparency

---

## 🏁 Summary

The Penalty Manager enforces **adaptive and intelligent security actions**, ensuring dynamic response to threats over time. It uses a reputation system, risk adjustment formula, and progressive escalation logic to determine final actions. The implementation is heavily optimized with Redis pipelines and fire-and-forget writes, but lacks persistence, whitelist support, and configurable thresholds for production scaling.

