# 🚦 Request Middleware (`request_middleware.py`)

## 📌 Purpose

The Request Middleware acts as the **primary entry point** of the API security system. It intercepts every incoming request before it reaches the application’s business logic and ensures that it is analyzed, evaluated, and processed according to security policies.

---

## ⚙️ Role

The middleware orchestrates the entire security pipeline:

- Intercepts all incoming HTTP requests
- Resolves identity using the Identity Resolver
- Extracts request signals (IP, endpoint, method, etc.)
- Builds behavioral features
- Invokes:
  - Risk Engine
  - Decision Engine
  - Penalty Manager
- Logs:
  - Request data
  - Risk scores
  - Decisions
  - ML explanations
- Returns final response action:
  - `allow`
  - `throttle`
  - `block`

---

## 🔄 Flow Integration

```
Incoming Request
      ↓
Request Middleware (this component)
      ↓
Identity Resolver
      ↓
Signals Extractor
      ↓
Feature Builder
      ↓
Risk Engine
      ↓
Decision Engine
      ↓
Penalty Manager
      ↓
Final Response
```

---

## 🎯 Why It Exists

Security must be enforced **before business logic execution**. This component ensures:

- Early threat detection
- Prevention of malicious requests reaching backend systems
- Centralized orchestration of all security components

---

## 🧠 Importance in the System

This is the **core execution pipeline controller**:

- Connects all modules into a unified flow
- Ensures consistent processing of every request
- Maintains system integrity and order

Without this component:

- The system becomes fragmented
- Security enforcement becomes inconsistent
- Integration between modules breaks down

---

## ⚠️ Design Considerations

- Must be **highly performant** (executes on every request)
- Fully **asynchronous** to avoid blocking
- Must handle failures gracefully (fallback decisions)
- Should minimize latency overhead

---

## 🚀 Future Enhancements

- Circuit breaker for Redis failures
- Request tracing (OpenTelemetry)
- Intelligent caching for repeated patterns
- Adaptive routing based on risk levels

---

## 🏁 Summary

The Request Middleware serves as the **central orchestration layer**, ensuring that every request is analyzed, evaluated, and enforced with security policies in real time.