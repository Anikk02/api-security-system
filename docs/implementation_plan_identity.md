# Multi-Signal Identity Fingerprinting for IP-Rotating Evaders

## The Problem

An attacker who rotates IPs breaks the current enforcement model in **two places**:

### 1. Fast-path block check (middleware)
```python
# state_manager.py — get_decision_signals()
pipe.exists(f"user:{user_id}:blocked")   # ← tied to user_id
pipe.exists(f"ip:{ip}:blocked")          # ← tied to a single IP
```
If the attacker rotates IPs, the second check never fires again.  
If they are anonymous (no API key), `user_id` is derived from `_generate_anonymous_fingerprint(ip)` — which is **also IP-only** — so the first check also stops working after a rotation.

### 2. Reputation system (penalty_manager)
```python
# penalty_manager.py
fingerprint = _generate_fingerprint(ip, ua)   # sha256(ip + ":" + ua)
rep_keys = [
    f"rep:ip:{ip}",
    f"rep:user:{user_id}",
    f"rep:fp:{fingerprint}"   # ← IP+UA only
]
```
IP rotation silently creates a fresh reputation slate.  
UA spoofing on top of IP rotation completely resets all three signals.

---

## What Stable Signals Are Actually Available

| Signal | Stable across IP rotation? | Spoofable? | Notes |
|---|---|---|---|
| `X-API-KEY` | ✅ Yes | Only if stolen | Best anchor for authenticated users |
| `User-Agent` | ⚠️ Usually | Yes, trivially | Useful combined, not alone |
| `X-Forwarded-For` / IP | ❌ No | Easily | The thing being rotated |
| Request timing pattern | ✅ Usually | Hard | Bots have mechanical intervals |
| Endpoint access pattern | ✅ Usually | Medium | Scraping paths are predictable |
| TLS JA3 fingerprint | ✅ Very | Hard | Not available here (no TLS termination in middleware) |
| Accept-Language header | ✅ Usually | Easy | Small added signal |
| Accept-Encoding header | ✅ Usually | Easy | Small added signal |

### Practical composite fingerprint for this system

```
behavioral_fingerprint = sha256(
    api_key_hash     ← strongest anchor (authenticated only)
    + ua_hash        ← device signal  
    + accept_lang    ← locale signal
    + accept_enc     ← client capability signal
)
```

For **anonymous users** (no API key), use:
```
behavioral_fingerprint = sha256(
    ua_hash
    + accept_lang
    + accept_enc
    + (endpoint_pattern_hash derived from first 3 endpoints visited)
)
```

This gives 3–4 independent signals instead of 1, making evasion require matching all of them simultaneously.

---

## Proposed Changes

### 1. [`resolver.py`](file:///c:/edb/api_security_system/backend/app/identity/resolver.py) — enrich `Identity`

Store a `behavioral_fingerprint` on the identity object derived from the stable request headers. This is computed once per request in the identity phase and passed through the entire pipeline.

#### What changes
- `Identity` gets a new field: `behavioral_fingerprint: str`  
- `resolve_identity` computes it from `X-API-KEY hash + UA + Accept-Language + Accept-Encoding`
- For anonymous users: `UA + Accept-Language + Accept-Encoding` (no IP involved)

---

### 2. [`state_manager.py`](file:///c:/edb/api_security_system/backend/app/state/state_manager.py) — check behavioral fingerprint in fast path

`get_decision_signals` currently checks 3–4 Redis keys. Add one more: `fp:{behavioral_fingerprint}:blocked`.

```python
# BEFORE: 4 pipeline commands
pipe.exists(f"user:{user_id}:blocked")
pipe.get(f"user:{user_id}:risk_score")
pipe.exists(f"user:{user_id}:throttled")
pipe.exists(f"ip:{ip}:blocked")

# AFTER: 5 pipeline commands (still 1 round-trip)
pipe.exists(f"user:{user_id}:blocked")
pipe.get(f"user:{user_id}:risk_score")
pipe.exists(f"user:{user_id}:throttled")
pipe.exists(f"ip:{ip}:blocked")
pipe.exists(f"fp:{behavioral_fingerprint}:blocked")   # ← NEW
```

A user rotating IPs is still caught if their behavioral fingerprint was blocked.

---

### 3. [`penalty_manager.py`](file:///c:/edb/api_security_system/backend/app/policy/penalty_manager.py) — use behavioral fingerprint, not IP+UA fingerprint

Replace `_generate_fingerprint(ip, ua)` with the `behavioral_fingerprint` passed in from identity. Also:
- Write `fp:{behavioral_fingerprint}:blocked` when a hard block fires
- Track `rep:fp:{behavioral_fingerprint}` reputation separately

```python
# BEFORE: fingerprint tied to IP+UA
fingerprint = _generate_fingerprint(ip, ua)   # sha256(ip:ua) ← changes on IP rotation

# AFTER: fingerprint comes from identity, tied to stable signals
fingerprint = identity.behavioral_fingerprint   # sha256(api_key+ua+accept_lang+...) ← stable
```

---

### 4. [`middleware` — `request_middleware.py`](file:///c:/edb/api_security_system/backend/app/middleware/request_middleware.py)

Pass `identity.behavioral_fingerprint` to `get_decision_signals` so the fast-path check can use it.

```python
# BEFORE
blocked, risk_score, throttled = await StateManager.get_decision_signals(
    identity.user_id,
    identity.ip_address
)

# AFTER
blocked, risk_score, throttled = await StateManager.get_decision_signals(
    identity.user_id,
    identity.ip_address,
    identity.behavioral_fingerprint   # ← new param
)
```

---

## Open Questions

> [!IMPORTANT]
> **Q1: How aggressive should fingerprint-only blocking be?**
>
> If we block on `fp:{fp}:blocked` in the fast path, a false positive (wrong fingerprint collision) could block a legitimate user who happens to share the same UA + Accept headers. SHA-256 makes collisions astronomically unlikely but not impossible at scale.
>
> Options:
> - **Option A (recommended)**: Block if fingerprint is blocked, same as IP block. Low risk — SHA-256 collision probability is negligible.
> - **Option B (conservative)**: Only throttle on fingerprint match, require IP match too for full block. Safer but easier to evade.

> [!NOTE]
> **Q2: Anonymous user fingerprint stability**
>
> For anonymous users with no API key, the fingerprint is UA + Accept headers only. A sophisticated attacker can spoof these trivially. However:
> - Most IP-rotating scripts don't bother rotating UA/headers
> - The endpoint access pattern hash (first 3 endpoints) adds a behavioral dimension that is harder to fake
>
> Do you want to include the endpoint pattern hash in the anonymous fingerprint? It requires one extra Redis read at identity time.

> [!NOTE]
> **Q3: API key hash vs raw API key in fingerprint**
>
> The fingerprint should use `sha256(api_key)`, not the raw key, so the raw key is never embedded in Redis key names.
> This is already how the anonymous fingerprint works — confirming this approach for authenticated users too.

---

## Files Changed

| File | Change |
|---|---|
| `identity/resolver.py` | Compute `behavioral_fingerprint`, store on `Identity` |
| `state/state_manager.py` | Add `fp:{fp}:blocked` check to `get_decision_signals` |
| `policy/penalty_manager.py` | Use `identity.behavioral_fingerprint` instead of `_generate_fingerprint(ip, ua)`, write `fp:{fp}:blocked` on hard block |
| `middleware/request_middleware.py` | Pass fingerprint to `get_decision_signals` |

## Verification Plan

### Manual
- Block a user by API key. Have them rotate IPs. Verify they are still blocked via fingerprint.
- Block an anonymous user. Have them rotate IPs. Verify they are still throttled via behavioral fingerprint.
- Verify the `rep:fp:{fp}` reputation key accumulates across IP rotations in Redis.

### Automated (existing pipeline)
- The background `analysis_pipeline` already logs `ip_changes` as a feature — after this change, high `ip_changes` + stable fingerprint = confirmed evasion attempt, feeding the risk score correctly.
