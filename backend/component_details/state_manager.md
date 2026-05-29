# 🧠 State Manager (`state_manager.py`)

## 📌 Purpose

The State Manager provides **real-time behavioral state management** using Redis.

---

## ⚙️ Role

- Tracks:
  - Request timestamps (sliding windows)
  - Error counts
  - Violations
  - Endpoint usage
- Handles:
  - Rate limiting
  - User/IP blocking
- Provides fast read/write operations for all components

---

## 🔄 Flow Integration

```
Middleware / Risk Engine / Penalty Manager
            ↓
       State Manager (this component)
            ↓
             Redis
```

---

## 🎯 Why It Exists

Behavioral security requires **low-latency state tracking**, which traditional databases cannot provide.

---

## 🧠 Importance in the System

Acts as the **short-term memory**:

- Enables real-time decisions
- Supports sliding window calculations
- Powers anomaly detection

---

## ⚠️ Design Considerations

- Redis dependency (critical)
- TTL-based cleanup
- Must handle high concurrency

---

## 🚀 Future Enhancements

- Redis clustering
- Persistent backup layer
- Local memory fallback

---

## 🏁 Summary

The State Manager provides **fast, real-time behavioral data**, enabling intelligent and timely decisions.