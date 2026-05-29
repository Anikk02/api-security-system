# 📊 Dashboard API (`dashboard.py`)

## 📌 Purpose

The Dashboard API provides **visibility, analytics, and control** over the security system, enabling clients to monitor and manage their API traffic.

---

## ⚙️ Role

### 🔹 Analytics
- Requests per second (RPS)
- Traffic trends
- Violation statistics

### 🔹 Monitoring
- Suspicious users
- Active threats
- Alerts (block/throttle events)

### 🔹 Logs
- Decision logs
- Request history
- Risk scores and explanations

### 🔹 User Control
- Block user
- Unblock user
- Send warnings

### 🔹 User Insights
- Risk score
- Activity patterns
- IP history

---

## 🔄 Flow Integration

```
Database + Redis
      ↓
Dashboard API (this component)
      ↓
Frontend Dashboard
```

---

## 🎯 Why It Exists

To transform the system from a backend service into a **usable SaaS product with transparency and control**.

---

## 🧠 Importance in the System

Provides:

- Observability (what is happening)
- Transparency (why decisions are made)
- Control (manual intervention)

Without this component:

- System becomes a black box
- Users cannot trust or manage it effectively

---

## ⚠️ Design Considerations

- Must handle large-scale data efficiently
- Requires pagination for logs
- Should minimize query latency

---

## 🚀 Future Enhancements

- Real-time updates via WebSockets
- Attack visualization dashboards
- Multi-tenant data isolation
- Billing and usage tracking

---

## 🏁 Summary

The Dashboard API acts as the **control and observability layer**, enabling users to monitor, understand, and manage the system effectively.