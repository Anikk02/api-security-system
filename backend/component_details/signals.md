# 📡 Request Signals Extractor (`signals.py`)

## 📌 Purpose

Extracts **raw request-level signals** from incoming HTTP requests.

---

## ⚙️ Role

- Parses request metadata from FastAPI `Request`
- Extracts:
  - IP address
  - User-Agent
  - Endpoint
  - HTTP method
  - Timestamp
- Normalizes into `RequestSignals`

---

## 🧱 Structure

```python
class RequestSignals:
    ip_address: str
    user_agent: str
    endpoint: str
    method: str
    timestamp: datetime
```

---

## 🔄 Flow Integration

```
Incoming Request
      ↓
Signals Extractor (this component)
      ↓
Feature Builder
      ↓
Risk Engine
```

---

## 🎯 Why It Exists

Provides **clean, standardized inputs** for all downstream components.

---

## 🧠 Importance in the System

Forms the **foundation of the intelligence pipeline**:

- Risk Engine depends on it
- Penalty Manager uses IP
- State Manager tracks behavior
- Logs rely on structured data

---

## ⚠️ Design Considerations

- Supports proxy environments
- Uses first IP in `X-Forwarded-For`
- Ensures UTC timestamps

---

## 🚀 Future Enhancements

- Geo-IP enrichment
- Advanced device fingerprinting
- Payload inspection

---

## 🏁 Summary

Acts as the **input normalization layer**, converting raw requests into structured data for analysis.