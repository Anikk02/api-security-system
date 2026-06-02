API Security System - Client Integration Guide
Table of Contents
What Is This System?

How It Works

Integration Methods

Step-by-Step Integration

What Gets Monitored

What Happens When an Attack Is Detected

Dashboard & Controls

API Reference for Clients

FAQ

1. What Is This System?
The API Security System is a middleware that sits between your users and your API to protect your backend from abuse, attacks, and malicious behavior.

In Simple Terms:
text
Without Our System:
User → Your API → Your Database (attackers waste your resources)

With Our System:
User → Our Middleware → Your API → Your Database (bad actors blocked before reaching you)
What We Protect Against:
Threat	How We Detect	Action Taken
Brute Force Attacks	Multiple rapid login attempts	Block IP/User for 1 hour
DDoS Attacks	Traffic bursts > normal	Throttle then block
API Abuse	Excessive requests	Rate limiting
Vulnerability Scanning	Endpoint probing patterns	Block scanner
Bot Traffic	Regular timing, no human patterns	Throttle
Credential Stuffing	Multiple auth attempts	Block
2. How It Works
2.1 High-Level Flow
text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOW OUR SYSTEM PROTECTS YOUR API                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User's Request                                                              │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    YOUR BACKEND                                       │    │
│  │                                                                        │    │
│  │  1. Our Middleware intercepts the request                             │    │
│  │     ├── Extracts: IP, User-Agent, Endpoint                            │    │
│  │     ├── Analyzes: Request rate, patterns, behavior                    │    │
│  │     └── Calculates: Risk score (0-100%)                               │    │
│  │                                                                        │    │
│  │  2. Decision is made:                                                  │    │
│  │     ├── Low Risk (<40%) → ALLOW (pass to your API)                    │    │
│  │     ├── Medium Risk (40-70%) → THROTTLE (small delay + warning)       │    │
│  │     └── High Risk (>70%) → BLOCK (reject immediately)                 │    │
│  │                                                                        │    │
│  │  3. Your API only receives ALLOWED requests                            │    │
│  │     └── Blocked requests never reach your business logic              │    │
│  │                                                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │                                                                      │
│       ▼                                                                      │
│  Response to User (or 429 Blocked)                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
2.2 What Happens to Blocked Requests
text
Attack Request → Our Middleware → Detects Attack → Returns 429
                                                    │
                                                    ▼
                                    Your API NEVER receives it
                                    Your resources are SAVED
3. Integration Methods
3.1 Method 1: Python/FastAPI Middleware (Recommended)
Best for: Python backend (FastAPI, Django, Flask)

python
# STEP 1: Install our SDK
pip install api-security-middleware

# STEP 2: Add ONE line to your FastAPI app
from api_security import SecurityMiddleware

app.add_middleware(
    SecurityMiddleware,
    api_key="your_api_key_here"  # Get from dashboard
)

# That's it! Your API is now protected
3.2 Method 2: API Gateway (Any Backend)
Best for: Any language (Node.js, Go, Java, PHP, Ruby)

text
Step 1: Get your gateway URL
https://gateway.api-security.com/your-company-name/

Step 2: Update your DNS or API endpoint
Before: api.yourcompany.com → Your Server
After:  api.yourcompany.com → CNAME → gateway.api-security.com

Step 3: Add API key to your server configuration (one-time)
3.3 Method 3: Reverse Proxy (Nginx)
Best for: Existing Nginx setups

nginx
# Add to your nginx.conf
location /api/ {
    # Send traffic through our security gateway
    proxy_pass https://gateway.api-security.com/your-company/;
    
    # Pass original request details
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-API-Key "your_api_key";
}
4. Step-by-Step Integration
4.1 Sign Up & Get API Key
text
1. Visit our dashboard: https://dashboard.api-security.com
2. Create an account
3. Add your API (provide: name, domain, estimated traffic)
4. Get your unique API key: sk_live_xxxxx
4.2 Choose Integration Method
Option A: Python Middleware (2 lines of code)
python
# Your existing FastAPI code (NO CHANGES to your business logic)
from fastapi import FastAPI

app = FastAPI()

# Your existing endpoints - NOTHING changes here
@app.get("/api/users")
def get_users():
    return {"users": [...]}

@app.post("/api/login")  
def login(username, password):
    # Your existing login logic
    return {"token": "..."}

# ADD THIS ONE LINE at the end:
from api_security import SecurityMiddleware
app.add_middleware(SecurityMiddleware, api_key="sk_live_your_key")

# Your API is now protected!
Option B: SDK Integration (5 lines of code)
python
# Your existing FastAPI code
from fastapi import FastAPI

app = FastAPI()

# Initialize our security client
from api_security import APISecurity
security = APISecurity(api_key="sk_live_your_key")

# Add security check before processing requests
@app.middleware("http")
async def security_check(request, call_next):
    # Check if request is safe
    result = await security.check(request)
    
    if result.blocked:
        return JSONResponse(status_code=429, 
                           content={"error": result.reason})
    
    # Add request ID to response
    response = await call_next(request)
    response.headers["X-Request-ID"] = result.request_id
    return response

# Your existing endpoints remain unchanged
4.3 Verify Integration
bash
# Test with a normal request
curl https://api.yourcompany.com/api/test
# Response: {"status": "ok"}  (with extra headers)

# Test with an attack (simulated)
curl -X POST https://api.yourcompany.com/login \
  -d '{"username":"admin","password":"wrong"}' \
  -H "X-Attack-Simulation: true"
# Response: 429 Too Many Requests
5. What Gets Monitored
5.1 Data We Collect (Meta-data only)
Data Point	Purpose	Example
IP Address	Location, abuse patterns	192.168.1.1
User-Agent	Bot detection	Mozilla/5.0...
Endpoint Path	Access patterns	/api/login
HTTP Method	Request type	POST
Timestamp	Rate calculation	2024-01-01T00:00:00Z
Response Status	Error rate tracking	200, 404, 429
5.2 Data We NEVER Collect
Data Type	Reason
Request Body	Privacy, security
Passwords	Never stored
Tokens/JWT	Not required
Database queries	Not needed
Customer PII	Not our business
5.3 Where Data Goes
text
Your Request → Our Middleware → Analyzed → Decisions Logged → Dashboard
                                      │
                                      ▼
                              Your API (only allowed requests)
                              We NEVER share your data with third parties
6. What Happens When an Attack Is Detected
6.1 Attack Detection Flow
text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME ATTACK RESPONSE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Attacker: 100 login attempts in 10 seconds                                 │
│       │                                                                      │
│       ▼                                                                      │
│  Our Middleware detects:                                                     │
│  ├── Request rate: 600/min (normal: 10/min)                                 │
│  ├── Pattern: Same endpoint repeated                                        │
│  └── Risk score: 92% (Critical)                                             │
│       │                                                                      │
│       ▼                                                                      │
│  Decision: BLOCK for 1 hour                                                 │
│       │                                                                      │
│       ▼                                                                      │
│  Response to attacker:                                                       │
│  HTTP 429 Too Many Requests                                                 │
│  {                                                                           │
│    "error": "Too many login attempts",                                      │
│    "retry_after": 3600,                                                     │
│    "reason": "Brute force pattern detected"                                 │
│  }                                                                           │
│       │                                                                      │
│       ▼                                                                      │
│  Your API receives: NOTHING (request blocked)                               │
│                                                                              │
│  Dashboard alert: "Attack blocked from IP 192.168.1.100"                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
6.2 Automatic Actions
Situation	Automatic Action	Duration
Rate limit exceeded (100 req/min)	Throttle (slow down)	5 minutes
Login failures > 10/minute	Block IP	10 minutes
Scanning endpoints	Block user	30 minutes
DDoS pattern detected	Block IP range	1 hour
Repeated violations	Increase block duration	Escalating
6.3 Manual Actions (You Control)
Via Dashboard, you can:

text
1. Block any user instantly (click BLOCK button)
2. Send warning to suspicious users
3. Whitelist trusted IPs
4. Adjust rate limits per endpoint
5. View attack patterns in real-time
7. Dashboard & Controls
7.1 What You See
text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          YOUR DASHBOARD                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                          │
│  │ Requests/   │ │ Violations  │ │ Suspicious  │                          │
│  │ Second: 47  │ │ Today: 1,234│ │ Users: 12   │                          │
│  └─────────────┘ └─────────────┘ └─────────────┘                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     LIVE THREAT MAP                                   │    │
│  │  [World map showing attack origins]                                  │    │
│  │  🔴 USA: 234 attacks  🟡 Europe: 89 attacks  🟢 Asia: 45 attacks    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     SUSPICIOUS USERS                                  │    │
│  │  User ID              │ IP            │ Score │ Action               │    │
│  │  ─────────────────────────────────────────────────────────────────   │    │
│  │  Bot-10554096         │ 192.168.1.1   │ 88%   │ [BLOCK] [WARN]       │    │
│  │  Attacker-123         │ 10.0.0.45     │ 95%   │ [BLOCK] [WARN]       │    │
│  │  user@malicious.com   │ 172.16.0.23   │ 76%   │ [BLOCK] [WARN]       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     RECENT ALERTS                                     │    │
│  │  [13:45:23] 🚨 Brute force attack blocked from 192.168.1.1          │    │
│  │  [13:42:10] ⚠️  Rate limit exceeded for user-12345                  │    │
│  │  [13:38:05] 🚨 Scanner detected probing /admin endpoint             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
7.2 Actions You Can Take
Action	What It Does	When To Use
Block User	Instantly blocks the user from accessing your API	Confirmed malicious activity
Send Warning	Sends notification to user	Suspicious but not confirmed
Whitelist IP	Always allow this IP	Trusted partners, internal systems
Adjust Limits	Change rate limits per endpoint	Legitimate high-volume APIs
View Details	See full request history	Investigation
8. API Reference for Clients
8.1 Security Headers We Add
Every request that reaches your API will have these headers:

http
X-Request-ID: req_abc123def456
X-Risk-Score: 0.23
X-Session-ID: fp_xyz789
8.2 Block Response (What your users see)
When a request is blocked, the user receives:

json
HTTP 429 Too Many Requests
{
    "error": "Too many requests",
    "message": "Suspicious activity detected",
    "retry_after": 3600,
    "request_id": "req_abc123def456"
}
8.3 Webhook Events (Optional)
We can send you webhooks for important events:

json
POST https://your-api.com/webhook/security
{
    "event": "user_blocked",
    "user_id": "user-12345",
    "reason": "Brute force detected",
    "ip": "192.168.1.100",
    "timestamp": "2024-01-01T00:00:00Z",
    "duration": 3600
}