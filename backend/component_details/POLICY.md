# Policy System

> A high-performance, adaptive request evaluation engine that transforms real-time risk signals, historical behavior, and identity reputation into security decisions (**ALLOW**, **THROTTLE**, or **BLOCK**).

---

# Table of Contents

1. Overview
2. Design Goals
3. High-Level Architecture
4. Request Lifecycle
5. Core Components
6. Trust Score
7. Adaptive Thresholds
8. Policy Decision Flow
9. Reputation System
10. Redis Data Model
11. Request Walkthroughs
12. Performance Optimizations
13. Design Principles
14. Configuration
15. Summary

---

# 1. Overview

The **Policy System** is the decision-making layer of the API Security Platform.

While the Analysis Pipeline determines **how risky** a request is, the Policy System determines **what action should be taken**.

It combines:

* Current request risk
* Historical request behavior
* Identity reputation
* IP reputation
* Fingerprint reputation
* Request volume
* Error history
* IP rotation
* Previous policy decisions

into a single security decision.

The system produces one of three actions:

| Action       | Description                                    |
| ------------ | ---------------------------------------------- |
| **ALLOW**    | Request is considered safe.                    |
| **THROTTLE** | Request is temporarily rate-limited.           |
| **BLOCK**    | Request is denied and the identity is blocked. |

Unlike traditional rate limiters that rely on request counts alone, this system evaluates **behavior over time**, allowing it to distinguish legitimate high-volume users from malicious traffic.

---

# 2. Design Goals

The Policy System was designed with the following goals.

## Adaptive

Thresholds should adapt to each client's historical behavior instead of relying on fixed values.

---

## Explainable

Every decision should be explainable.

Instead of simply returning:

```text
BLOCK
```

the system can explain:

* Why the request was blocked
* Which signals contributed most
* Current trust score
* Current suspicion score
* Reputation penalties
* Thresholds used

This makes debugging and auditing significantly easier.

---

## Stateless Business Logic

Business logic should remain completely independent from storage.

Each engine operates only on a **PenaltyContext** and returns a **PenaltyDecision**.

This makes every component easy to:

* Test
* Mock
* Replace
* Extend

---

## High Performance

Each request should require:

* One Redis read pipeline
* One Redis write pipeline

No component should perform direct Redis operations except the repository layer.

---

## Progressive Enforcement

Instead of immediately blocking suspicious users, the system gradually escalates penalties.

```text
Normal User

        │

        ▼

ALLOW

        │

Suspicious Behaviour

        │

        ▼

THROTTLE

        │

Repeated Abuse

        │

        ▼

BLOCK
```

This significantly reduces false positives while still protecting the API.

---

# 3. High-Level Architecture

```text
                    Incoming Request
      (Identity + Signals + Risk Score)
                    │
                    ▼
             PenaltyManager
          (Workflow Orchestrator)
                    │
                    ▼
         RedisRepository.load_context()
                    │
                    ▼
              TrustEngine
                    │
                    ▼
      AdaptiveThresholdEngine
                    │
                    ▼
              PolicyEngine
                    │
                    ▼
             RecoveryEngine
                    │
                    ▼
      RedisRepository.apply_decision()
                    │
                    ▼
            Final Policy Decision
```

Each component has a single responsibility.

| Component               | Responsibility                    |
| ----------------------- | --------------------------------- |
| PenaltyManager          | Coordinates the complete workflow |
| RedisRepository         | Reads and writes Redis state      |
| TrustEngine             | Calculates trust score            |
| AdaptiveThresholdEngine | Learns client-specific thresholds |
| PolicyEngine            | Makes enforcement decisions       |
| RecoveryEngine          | Rewards sustained good behavior   |

No component contains responsibilities belonging to another component.

---

# 4. Request Lifecycle

Every incoming request follows the same sequence.

## Step 1 — Request Arrives

The Analysis Pipeline has already completed its work and produced a risk score.

Example:

```json
{
  "client_id": 12345,
  "identity_id": "user_alice",
  "ip_address": "192.168.1.100",
  "fingerprint": "fp_hash",
  "risk_score": 0.18
}
```

The Policy System does **not** calculate risk.

Its job begins after the risk score is available.

---

## Step 2 — Load Historical Context

The first operation is loading all historical state from Redis.

A single pipelined read fetches:

* Request history
* Error count
* Violation count
* Reputation scores
* Cached risk score
* Block status
* Throttle status
* IP rotation history

This information is assembled into a single immutable object:

```python
PenaltyContext
```

Every engine receives this same context.

---

## Step 3 — Calculate Trust

The Trust Engine evaluates all available signals and produces a trust score.

Example:

```text
Trust Score

=
1.0
− Risk Penalty
− Reputation Penalty
− Violation Penalty
− Volume Penalty
− Error Penalty
− IP Rotation Penalty
+ Recovery Bonus
```

Higher trust indicates healthier behaviour.

Lower trust indicates suspicious behaviour.

---

## Step 4 — Calculate Suspicion

The Policy Engine does not work directly with trust.

Instead it converts trust into suspicion.

```text
Suspicion Score

=

1 − Trust Score
```

Example:

```text
Trust Score

0.83

↓

Suspicion Score

0.17
```

A lower suspicion score indicates safer behaviour.

---

## Step 5 — Load Adaptive Thresholds

Instead of using fixed thresholds, the Adaptive Threshold Engine retrieves thresholds learned from the client's historical behaviour.

For example:

```text
Medium Threshold

0.48

High Threshold

0.74
```

Different clients may receive different thresholds depending on their historical traffic patterns.

---

## Step 6 — Make Policy Decision

The Policy Engine evaluates rules in priority order.

The first matching rule determines the final action.

For example:

```text
Already Blocked?

↓

Yes

↓

BLOCK
```

or

```text
Suspicion ≥ High Threshold

↓

BLOCK
```

or

```text
Suspicion ≥ Medium Threshold

↓

THROTTLE
```

Otherwise:

```text
ALLOW
```

---

## Step 7 — Recovery

The Recovery Engine updates long-term behaviour.

Examples include:

* Increasing reputation penalties after abuse
* Slowly recovering reputation after clean behaviour
* Clearing expired throttles
* Applying recovery bonuses

The Recovery Engine never changes the decision itself.

It only adjusts future behaviour.

---

## Step 8 — Persist State

Finally, RedisRepository performs a single pipelined write.

Possible updates include:

* Store request timestamp
* Update request count
* Update reputation
* Cache risk score
* Increment violations
* Apply throttle
* Apply block
* Track IP rotation

After persistence completes, the final decision is returned to the caller.

---

# 5. Core Components

## PenaltyManager

The PenaltyManager is the orchestration layer of the Policy System.

It intentionally contains **no business logic**.

Its responsibility is simply to execute each stage in the correct order.

Workflow:

```text
Load Context
      │
      ▼
Calculate Trust
      │
      ▼
Load Thresholds
      │
      ▼
Policy Decision
      │
      ▼
Recovery
      │
      ▼
Persist Updates
      │
      ▼
Return Decision
```

Because it performs orchestration only, it is easy to understand, easy to maintain, and easy to extend.

---

## RedisRepository

RedisRepository is the only component allowed to communicate directly with Redis.

It exposes two high-level operations:

```python
load_context()
```

and

```python
apply_decision()
```

All Redis-specific implementation details remain isolated inside this component.

This separation keeps the policy engines completely storage-independent.

---

## TrustEngine

The Trust Engine converts historical behaviour into a single numerical trust score.

Its inputs include:

* Current risk score
* Reputation
* Violations
* Request volume
* Error count
* IP rotation
* Recovery bonus

The resulting trust score becomes the primary input to the Policy Engine.

---

# 6. Trust Score

The **Trust Engine** converts multiple behavioral signals into a single numerical score that represents how trustworthy an incoming request appears.

A higher trust score indicates that the request is more likely to be legitimate, while a lower score suggests suspicious or malicious behavior.

The score is always normalized to the range **[0.0, 1.0]**.

---

## Inputs

The Trust Engine evaluates the following signals.

| Signal         | Description                                                |
| -------------- | ---------------------------------------------------------- |
| Risk Score     | Output produced by the Analysis Pipeline                   |
| Reputation     | Historical reputation of the identity, IP, and fingerprint |
| Violations     | Previous policy violations                                 |
| Request Volume | Number of requests within the observation window           |
| Error Count    | Recent failed requests                                     |
| IP Rotation    | Number of unique IP addresses recently used                |
| Recovery Bonus | Reward for sustained clean behavior                        |

---

## Trust Formula

```text
trust_score
=
1.0
- (risk_score × 0.55)
- (combined_reputation × 0.20)
- min(violations × 0.015, 0.15)
- min(max(request_count - 40, 0) / 200, 0.05)
- min(error_count / 300, 0.05)
- min(unique_ip_count × 0.02, 0.10)
+ recovery_bonus
```

Finally,

```text
trust_score = clamp(trust_score, 0.0, 1.0)
```

This weighting gives the highest importance to the **current risk score**, while still considering historical behavior.

---

## Trust Levels

| Trust Score     | Level  | Meaning                       |
| --------------- | ------ | ----------------------------- |
| **≥ 0.80**      | HIGH   | User appears trustworthy      |
| **0.50 – 0.79** | MEDIUM | User is under observation     |
| **< 0.50**      | LOW    | User is considered suspicious |

The Trust Level itself does **not** determine the action. It is simply a human-readable representation of the numerical trust score.

---

## Why Multiple Signals?

Using only the current risk score can produce false positives.

For example:

* A legitimate user might suddenly perform many requests.
* A returning user may have a small anomaly but years of clean history.
* A bot may have a moderate risk score but a terrible reputation.

Combining multiple signals produces a much more reliable estimate of user behavior.

---

# 7. Adaptive Threshold Engine

Traditional security systems use fixed thresholds.

For example,

```text
Medium Threshold = 0.50
High Threshold   = 0.75
```

While simple, fixed thresholds fail to account for different client behaviors.

A payment gateway, for example, naturally experiences different traffic patterns than an internal administration API.

Instead, the Policy System learns thresholds independently for every client.

---

## Responsibilities

The Adaptive Threshold Engine is responsible for:

* Maintaining historical suspicion scores
* Learning client-specific thresholds
* Preventing threshold oscillation
* Providing sensible defaults for new clients

---

## Historical Window

Each client stores a rolling history of recent suspicion scores.

```text
Last 300 Suspicion Scores
```

Older values are automatically discarded so that thresholds continuously adapt to current behavior.

---

## Threshold Calculation

The engine calculates two thresholds.

| Threshold | Percentile      |
| --------- | --------------- |
| Medium    | 65th Percentile |
| High      | 85th Percentile |

For example,

```text
Historical Suspicion Scores

0.08
0.11
0.15
0.19
0.26
0.34
0.47
0.51
0.58
0.79
...
```

might produce

```text
Medium Threshold = 0.48

High Threshold = 0.73
```

---

## EWMA Smoothing

Thresholds should not fluctuate dramatically because of a few unusual requests.

To stabilize learning, the engine applies **Exponentially Weighted Moving Average (EWMA)** smoothing.

```text
α = 0.30
```

This allows thresholds to gradually adapt while ignoring short-lived spikes.

---

## Default Thresholds

When insufficient historical data exists, the engine falls back to predefined values.

```text
Medium Threshold = 0.50

High Threshold = 0.75
```

This ensures new clients receive reasonable protection immediately.

---

# 8. Policy Engine

The Policy Engine is responsible for making the final enforcement decision.

Unlike the Trust Engine, it performs **no scoring**.

Its only responsibility is evaluating policy rules.

---

## Suspicion Score

The Policy Engine first converts trust into suspicion.

```text
Suspicion Score

=

1 − Trust Score
```

Example

```text
Trust Score

0.83

↓

Suspicion Score

0.17
```

Higher suspicion corresponds to riskier behavior.

---

## Rule Evaluation

Rules are evaluated from highest priority to lowest priority.

The first matching rule determines the final action.

```text
Already Blocked?
        │
       Yes
        │
        ▼
      BLOCK
```

Otherwise,

```text
Already Throttled?
        │
       Yes
        │
        ▼
    THROTTLE
```

Otherwise,

```text
Unique IPs ≥ 5

AND

Suspicion ≥ Medium Threshold

↓

BLOCK
```

Otherwise,

```text
Unique IPs ≥ 3

AND

Suspicion ≥ Medium Threshold

↓

THROTTLE
```

Otherwise,

```text
Suspicion ≥ High Threshold

↓

BLOCK
```

Otherwise,

```text
Suspicion ≥ Medium Threshold

↓

THROTTLE
```

Otherwise,

```text
ALLOW
```

This ordering is intentional.

Some conditions (such as an existing block) should immediately terminate evaluation without checking later rules.

---

# 9. Recovery Engine

The Recovery Engine rewards users who consistently demonstrate healthy behavior.

Rather than permanently punishing suspicious activity, reputation gradually improves as users continue making legitimate requests.

---

## Responsibilities

The Recovery Engine may:

* Increase reputation penalties after abuse
* Reduce reputation after clean behavior
* Remove expired throttles
* Apply recovery bonuses

It never overrides the decision produced by the Policy Engine.

---

## Recovery Actions

| Decision                     | Recovery Action             |
| ---------------------------- | --------------------------- |
| BLOCK                        | Increase reputation penalty |
| THROTTLE                     | Small reputation increase   |
| ALLOW (Clean)                | Reduce reputation           |
| Previously Throttled + Clean | Remove throttle             |

This gradual recovery helps reduce long-term false positives while still discouraging repeated abuse.

---

# 10. Reputation System

The Policy System tracks reputation from multiple independent sources.

Instead of relying on a single identity, reputation is accumulated across several dimensions.

| Source                 | Purpose                               |
| ---------------------- | ------------------------------------- |
| IP Reputation          | Detect abusive IP addresses           |
| Identity Reputation    | Track long-term user behavior         |
| Fingerprint Reputation | Detect users changing IPs or accounts |

These values are combined into a single reputation score used by the Trust Engine.

Higher reputation values indicate more suspicious historical behavior.

Lower values indicate healthier behavior.

---

## Reputation Updates

After every decision, the Recovery Engine determines how reputation should change.

Typical behavior is:

| Decision | Reputation Effect |
| -------- | ----------------- |
| ALLOW    | Small decrease    |
| THROTTLE | Moderate increase |
| BLOCK    | Large increase    |

All reputation values remain clamped to the range:

```text
0.0 ≤ Reputation ≤ 1.0
```

This prevents values from growing indefinitely.

---

# 11. Redis Data Model

The Policy System stores only the state required to make future policy decisions.

Each key has a clearly defined purpose and a finite lifetime (TTL), ensuring that stale information is automatically removed without requiring manual cleanup.

---

## Request Activity

| Redis Key                                        | Type       | TTL    | Purpose                                                  |
| ------------------------------------------------ | ---------- | ------ | -------------------------------------------------------- |
| `client:{client}:identity:{identity}:timestamps` | Sorted Set | 30 min | Tracks request timestamps for request volume calculation |
| `client:{client}:identity:{identity}:ips`        | Set        | 5 min  | Tracks unique IPs for IP rotation detection              |
| `client:{client}:identity:{identity}:errors`     | Counter    | 30 min | Recent error count                                       |
| `client:{client}:identity:{identity}:violations` | Counter    | 30 min | Recent policy violations                                 |

---

## Cached State

| Redis Key                                        | TTL        | Purpose                 |
| ------------------------------------------------ | ---------- | ----------------------- |
| `client:{client}:identity:{identity}:risk_score` | 5 min      | Cache latest risk score |
| `client:{client}:identity:{identity}:blocked`    | 2–12 hours | Active block status     |
| `client:{client}:identity:{identity}:throttled`  | 60 seconds | Active throttle status  |

---

## Reputation

| Redis Key                       | TTL    |
| ------------------------------- | ------ |
| `rep:ip:{ip}`                   | 1 hour |
| `rep:identity:{identity}`       | 1 hour |
| `rep:fingerprint:{fingerprint}` | 1 hour |

---

## Global Blocks

| Redis Key                  | Purpose                    |
| -------------------------- | -------------------------- |
| `ip:{ip}:blocked`          | Block abusive IP addresses |
| `fp:{fingerprint}:blocked` | Block abusive fingerprints |

---

# 12. Request Walkthroughs

The following examples demonstrate how the Policy System transforms historical context into a final enforcement decision.

These examples intentionally show the scoring process so that every decision can be easily understood and verified.

---

# Example 1 — Normal Trusted User

A legitimate user makes their first request of the day.

## Incoming Request

```json
{
  "client_id": 12345,
  "identity_id": "user_alice",
  "risk_score": 0.05
}
```

---

## Historical Context

| Metric                 | Value |
| ---------------------- | ----: |
| Request Count          |     0 |
| Error Count            |     0 |
| Violations             |     0 |
| IP Reputation          |  0.00 |
| Identity Reputation    |  0.00 |
| Fingerprint Reputation |  0.00 |
| Unique IPs             |     0 |

---

## Trust Score Calculation

```text
trust
=
1.0
- (0.05 × 0.55)

= 0.9725
```

Trust Level

```text
HIGH
```

---

## Suspicion Score

```text
suspicion

=

1 − 0.9725

=

0.0275
```

---

## Thresholds

```text
Medium = 0.50

High = 0.75
```

---

## Decision

```text
0.0275 < 0.50

↓

ALLOW
```

### Why?

* Very low risk score
* No previous violations
* No reputation penalty
* No abnormal request volume
* No IP rotation

---

## Recovery

Since the request was clean, the Recovery Engine slightly rewards the user.

```text
reputation_delta = -0.02
```

The user's reputation gradually improves over time if clean behavior continues.

---

# Example 2 — Suspicious User

The user has accumulated poor reputation, several violations, and a high request rate.

## Incoming Request

```json
{
  "client_id": 12345,
  "identity_id": "user_eve",
  "risk_score": 0.92
}
```

---

## Historical Context

| Metric              | Value |
| ------------------- | ----: |
| Request Count       |   150 |
| Error Count         |    12 |
| Violations          |     4 |
| Combined Reputation |  0.69 |
| Unique IPs          |     2 |

---

## Trust Score Calculation

```text
trust

=

1.0
- (0.92 × 0.55)
- (0.69 × 0.20)
- (4 × 0.015)
- (110 / 200)
- (12 / 300)
- (2 × 0.02)

=

0.208
```

Trust Level

```text
LOW
```

---

## Suspicion Score

```text
1 − 0.208

=

0.792
```

---

## Adaptive Thresholds

```text
Medium = 0.48

High = 0.72
```

---

## Decision

```text
0.792 ≥ 0.72

↓

BLOCK
```

### Why?

* Very high risk score
* Poor historical reputation
* Multiple previous violations
* Extremely high request volume
* Large number of recent errors

The combination of these signals places the request well above the adaptive blocking threshold.

---

## Recovery

Blocking also increases future reputation penalties.

```text
reputation_delta = +0.20
```

This makes repeated abuse progressively more difficult.

---

# 13. Performance Optimizations

The Policy System is designed for low latency and minimal Redis overhead.

## Single Read Pipeline

All request state is loaded using a single Redis pipeline.

Instead of multiple network round trips, every required value is fetched together before policy evaluation begins.

---

## Single Write Pipeline

All updates are persisted together after the decision has been made.

This includes:

* Request history
* Reputation updates
* Violation counters
* Cached risk score
* Block status
* Throttle status
* IP rotation tracking

---

## Stateless Components

All engines operate on in-memory objects.

They never communicate with Redis directly.

This separation greatly improves:

* Testability
* Maintainability
* Performance

---

## Automatic Cleanup

Every Redis key has a TTL.

Expired request history, throttles, cached scores, and temporary state disappear automatically without background cleanup jobs.

---

# 14. Design Principles

The Policy System follows several architectural principles.

## Single Responsibility

Every component performs exactly one job.

| Component               | Responsibility         |
| ----------------------- | ---------------------- |
| PenaltyManager          | Workflow orchestration |
| RedisRepository         | Redis operations       |
| TrustEngine             | Trust calculation      |
| AdaptiveThresholdEngine | Threshold learning     |
| PolicyEngine            | Decision making        |
| RecoveryEngine          | Reputation recovery    |

---

## Explainability

Every decision can be explained using:

* Trust score
* Suspicion score
* Thresholds
* Reputation
* Historical behavior
* Decision reason

This makes debugging and auditing straightforward.

---

## Progressive Enforcement

Rather than immediately blocking suspicious behavior, the system gradually escalates enforcement.

```text
ALLOW

↓

THROTTLE

↓

BLOCK
```

This reduces false positives while still protecting the API.

---

## Adaptive Security

Thresholds evolve with client behavior.

A client with consistently higher legitimate traffic is evaluated differently from one with historically low traffic, reducing unnecessary enforcement while maintaining security.

---

# 15. Summary

The Policy System transforms a collection of behavioral signals into consistent, explainable security decisions.

By combining real-time risk scores with historical behavior, adaptive thresholds, reputation tracking, and progressive enforcement, it provides stronger protection than traditional fixed-rule rate limiters.

The architecture emphasizes:

* Clear separation of responsibilities
* Minimal Redis operations
* Adaptive decision making
* Explainable scoring
* Gradual reputation recovery
* High performance
* Easy testing and maintenance

Together, these components enable the Policy System to accurately distinguish between legitimate users and abusive behavior while remaining scalable, maintainable, and suitable for production environments.

---

**End of Document**


