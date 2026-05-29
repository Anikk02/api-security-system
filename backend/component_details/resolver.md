# 🧍 Identity Resolver (`resolver.py`)

## 📌 Purpose

The Identity Resolver is responsible for assigning a **unique and consistent identity** to every incoming request, enabling user tracking and behavior analysis.

---

## ⚙️ Role

- Extracts API key from request headers
- Validates API key against the database
- Assigns:
  - Authenticated identity (user_id)
  - OR anonymous identity (IP-based fingerprint)
- Extracts client IP:
  - Supports `X-Forwarded-For`
  - Falls back to direct client IP

---

## 🧱 Structure

```python
class Identity:
    user_id: int
    api_key: str | None
    is_anonymous: bool
```

---

## 🔄 Flow Integration

```
Request Middleware
      ↓
Identity Resolver (this component)
      ↓
Signals + Feature Processing
```

---

## 🎯 Why It Exists

Behavior-based security requires **consistent identity mapping** across requests.

---

## 🧠 Importance in the System

Enables:

- User-level behavior tracking
- Rate limiting per identity
- Reputation scoring
- Targeted blocking

Without identity:

- Behavior tracking becomes unreliable
- Security decisions lose precision

---

## ⚠️ Design Considerations

- Anonymous users handled via hashed IP
- API key lookup must be efficient (avoid DB bottlenecks)
- Proxy IP extraction must be accurate

---

## 🚀 Future Enhancements

- API key hashing for security
- JWT-based authentication
- Multi-device identity tracking

---

## 🏁 Summary

The Identity Resolver provides the **foundation for user-aware security**, enabling accurate tracking, analysis, and enforcement.