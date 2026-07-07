# 📊 Dashboard API (`dashboard.py`)

## 📌 Purpose

The Dashboard API provides **visibility, analytics, and control** over the security system, enabling clients to monitor and manage their API traffic in real time.

---

## ⚙️ Core Responsibilities

### 🔹 Real-time Analytics
- Requests per second (RPS) with trend calculation
- Traffic composition (normal / suspicious / high-risk)
- Violation detection trends (15-minute windows)

### 🔹 Threat Monitoring
- Suspicious users list (medium+ risk scores)
- Active alerts for high-risk threats
- IP risk trend analysis (1-hour)

### 🔹 Audit & Logs
- Paginated decision logs with explanations
- Request history with risk scoring
- Full transparency into security actions (allow/block/throttle)

### 🔹 User Management & Control
- Block/unblock users (Redis-backed state)
- Send warnings to users
- View detailed user risk profiles

### 🔹 Granular User Insights
- Current and average risk scores (last 15 min)
- Recent actions with reasons
- IP address history

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


---

## 🎯 Why It Exists

To transform the security engine from a black box into a **transparent, actionable SaaS product** — enabling administrators to see threats, understand decisions, and intervene manually when needed.

---

## 🧠 System Importance

Without this component:

- The system becomes unobservable
- No way to audit decisions or understand user risk
- Cannot manually block or warn users
- Reduced trust in automated security

With this component:

- Full observability into traffic and threats
- Clear risk explanations for each decision
- Manual override capabilities (block/unblock)
- Data-driven insights for security teams

---

## ⚙️ Technical Highlights

### Optimized Database Queries
- **Single-pass aggregations** for RPS, violations, and risk composition
- **Time-bucketed traffic data** using `date_trunc` (minute/hour)
- **Re-bucketing for 1-hour views** (5-minute slots)
- **Join reduction** — minimal round trips to PostgreSQL

### Adaptive Thresholds
- Uses `get_adaptive_thresholds()` from the risk engine
- `high_th` (critical risk) and `med_th` (suspicious risk)
- Violations always count **medium + high** risk scores

### Redis Integration
- User block state stored in Redis (`StateManager`)
- Fast lookup for `is_blocked` status without touching DB

### Pagination & Performance
- Logs support pagination (`page`, `limit`)
- Suspicious users limited (default 10, max 50)
- All time-window queries use indexed `created_at` filters

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Main dashboard stats (RPS, violations, trends) |
| GET | `/api/dashboard/traffic` | Time-series traffic data (15m/1h/24h) |
| GET | `/api/dashboard/suspicious-users` | List of users with medium+ risk |
| GET | `/api/dashboard/alerts` | Recent high-risk alerts |
| GET | `/api/dashboard/logs` | Paginated decision logs |
| GET | `/api/dashboard/user/{user_id}` | Detailed user risk profile |
| GET | `/api/dashboard/ip/{ip}/trend` | Risk trend for a specific IP (last hour) |
| POST | `/api/dashboard/user/{user_id}/block` | Block a user (with duration) |
| POST | `/api/dashboard/user/{user_id}/unblock` | Unblock a user |
| POST | `/api/dashboard/user/{user_id}/warning` | Send warning to a user |

---

## 🚀 Future Enhancements (Suggested)

- Real-time WebSocket push for new alerts
- Geographic threat heatmaps
- Multi-tenant isolation for enterprise customers
- Exportable audit reports (CSV/JSON)
- Automated response rules (e.g., auto-block after X violations)

---

## 🏁 Summary

The Dashboard API is the **control plane and observability layer** of the security system. It bridges raw detection data with human-understandable insights and manual controls, making the system trustworthy and manageable in production environments.