import asyncio
import random
import httpx
import time
from typing import List, Dict

BASE_URL = "http://localhost:8000"

# ENHANCED REALISTIC USER AGENTS
USER_AGENTS = {
    "browser": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    ],
    "mobile": [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    ],
    "attack_tool": [
        "sqlmap/1.7.11#dev",
        "Nmap Scripting Engine",
        "nikto/2.5.0",
        "curl/7.68.0",
        "python-requests/2.31.0",
        "Hydra/9.3",
        "Go-http-client/1.1",
    ]
}

# EXPANDED ENDPOINTS for more attack surface
NORMAL_ENDPOINTS = [
    "/api/data",
    "/api/test", 
    "/api/profile",
    "/api/users/me",
    "/health",
    "/api/products",
    "/api/search"
]

SENSITIVE_ENDPOINTS = [
    "/login",
    "/admin",
    "/admin/dashboard",
    "/api/admin/users",
    "/config",
    "/api/internal/metrics",
    "/reset-password",
    "/.git/config",
    "/backup/db.sql",
    "/.env",
    "/debug",
    "/api/private",
    "/graphql",
    "/phpmyadmin",
    "/api/v2/internal",
    "/swagger-ui.html"
]

def random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def get_user_agent(user_type):
    """Return realistic user agent based on user type"""
    if user_type == "normal":
        return random.choice(USER_AGENTS["browser"] + USER_AGENTS["mobile"])
    elif user_type == "suspicious":
        return random.choice(USER_AGENTS["browser"])  # Suspicious users hide in browsers
    else:  # attack
        return random.choice(USER_AGENTS["attack_tool"] + USER_AGENTS["browser"])

def random_headers(user_type, rotate_ip=True):
    headers = {
        "User-Agent": get_user_agent(user_type),
        "Accept": random.choice(["application/json", "*/*"]),
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "X-Simulated-Label": user_type
    }
    
    if rotate_ip:
        headers["X-Forwarded-For"] = random_ip()
    
    # Add attack-specific headers
    if user_type == "attack":
        headers["X-Scanner"] = random.choice(["sqlmap", "nikto", "nmap"])
        headers["X-Requested-With"] = "XMLHttpRequest"
    
    return headers

# ============ EXTREME AGGRESSIVE ATTACKS ============

async def normal_user(user_id):
    """Normal user - unchanged for baseline"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
        sessions = random.choices(NORMAL_ENDPOINTS, k=random.randint(3, 8))
        
        for req_num in range(random.randint(30, 80)):  # Reduced for faster completion
            if req_num % random.randint(5, 15) == 0:
                endpoint = random.choice(sessions)
            else:
                endpoint = random.choice(NORMAL_ENDPOINTS)
            
            try:
                await client.get(endpoint, headers=random_headers("normal"))
            except:
                pass
            
            if random.random() < 0.2:
                await asyncio.sleep(random.uniform(1.0, 3.0))
            else:
                await asyncio.sleep(random.uniform(0.5, 1.5))

async def aggressive_brute_force(user_id):
    """EXTREME: High-speed brute force attack"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=3) as client:
        usernames = ["admin", "root", "administrator", "test", "user", "system"]
        common_passwords = [
            "admin123", "password123", "123456", "qwerty", "admin", 
            "root", "toor", "passw0rd", "letmein", "welcome",
            "123456789", "password", "12345", "adminadmin"
        ]
        
        for attempt in range(random.randint(300, 500)):  # More attempts
            username = random.choice(usernames)
            password = random.choice(common_passwords)
            
            try:
                await client.post(
                    "/login",
                    json={"username": username, "password": password},
                    headers=random_headers("attack", rotate_ip=True),
                    timeout=2
                )
            except:
                pass
            
            # Extremely fast (5-15ms between attempts)
            await asyncio.sleep(random.uniform(0.005, 0.015))

async def aggressive_scanner(user_id):
    """EXTREME: Rapid vulnerability scanner"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=3) as client:
        all_paths = SENSITIVE_ENDPOINTS + [
            "/wp-admin", "/phpmyadmin", "/.env", "/backup.zip",
            "/api/v2", "/graphql", "/swagger.json", "/openapi.json",
            "/actuator/health", "/actuator/env", "/metrics", "/trace",
            "/dump", "/.aws/credentials", "/.ssh/id_rsa", "/password.txt"
        ]
        
        for _ in range(random.randint(300, 400)):
            endpoint = random.choice(all_paths)
            
            try:
                # Try multiple HTTP methods
                method = random.choice(["GET", "POST", "PUT", "DELETE", "HEAD"])
                if method == "GET":
                    await client.get(endpoint, headers=random_headers("attack"), timeout=2)
                elif method == "POST":
                    await client.post(endpoint, json={"test": "' OR '1'='1"}, headers=random_headers("attack"), timeout=2)
                else:
                    await client.request(method, endpoint, headers=random_headers("attack"), timeout=2)
            except:
                pass
            
            # Very fast scanning (10-30ms)
            await asyncio.sleep(random.uniform(0.01, 0.03))

async def ddos_burst(user_id):
    """EXTREME: DDoS-style burst attack"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=2) as client:
        # Target resource-intensive endpoints
        targets = ["/api/data", "/api/search", "/api/products", "/api/users/me"]
        endpoint = random.choice(targets)
        
        for _ in range(random.randint(500, 800)):
            try:
                await client.get(
                    endpoint,
                    headers=random_headers("attack", rotate_ip=False),  # Same IP for burst
                    timeout=1
                )
            except:
                pass
            
            # Almost no delay (1-5ms)
            await asyncio.sleep(random.uniform(0.001, 0.005))

async def sql_injection_attack(user_id):
    """EXTREME: SQL injection attempts"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=3) as client:
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users--",
            "admin'--",
            "1' OR '1' = '1",
            "' OR 1=1--",
            "'; SELECT * FROM passwords--",
            "' OR 'x'='x",
            "1; DROP TABLE users",
            "' AND SLEEP(5)--"
        ]
        
        for _ in range(random.randint(200, 350)):
            payload = random.choice(sql_payloads)
            
            try:
                if random.random() > 0.5:
                    # Query parameter injection
                    await client.get(
                        f"/api/search?q={payload}",
                        headers=random_headers("attack"),
                        timeout=2
                    )
                else:
                    # POST body injection
                    await client.post(
                        "/login",
                        json={"username": payload, "password": payload},
                        headers=random_headers("attack"),
                        timeout=2
                    )
            except:
                pass
            
            await asyncio.sleep(random.uniform(0.005, 0.02))

async def endpoint_fuzzer(user_id):
    """EXTREME: Fuzzing random endpoints"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=2) as client:
        prefixes = ["api", "admin", "internal", "private", "v1", "v2", "test", "dev", "stage"]
        suffixes = ["", "/admin", "/config", "/backup", "/old", "/temp", "/secret", "/hidden"]
        
        for _ in range(random.randint(300, 450)):
            # Generate random paths
            endpoint = f"/{random.choice(prefixes)}/{random.randint(1,999)}{random.choice(suffixes)}"
            
            try:
                await client.get(
                    endpoint,
                    headers=random_headers("attack"),
                    timeout=2
                )
            except:
                pass
            
            await asyncio.sleep(random.uniform(0.005, 0.015))

async def credential_stuffing_aggressive(user_id):
    """EXTREME: Rapid credential stuffing"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=3) as client:
        creds = [
            ("admin", "admin123"), ("admin", "password123"), ("admin", "123456"),
            ("root", "root"), ("root", "toor"), ("root", "123456"),
            ("user", "user"), ("user", "password"), ("user", "123456"),
            ("test", "test"), ("test", "test123"), ("test", "123456"),
        ]
        
        for _ in range(random.randint(250, 400)):
            username, password = random.choice(creds)
            
            # Use browser user agents to hide
            headers = {
                "X-Forwarded-For": random_ip(),
                "User-Agent": random.choice(USER_AGENTS["browser"]),
                "Accept": "application/json",
                "X-Simulated-Label": "attack"
            }
            
            try:
                await client.post("/login", json={"username": username, "password": password}, headers=headers, timeout=2)
            except:
                pass
            
            await asyncio.sleep(random.uniform(0.01, 0.03))

async def rapid_fire(user_id):
    """EXTREME: Maximum speed attack"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=1) as client:
        for _ in range(random.randint(800, 1200)):
            try:
                await client.get(
                    "/api/test",
                    headers=random_headers("attack", rotate_ip=False),
                    timeout=0.5
                )
            except:
                pass
            
            # Sub-millisecond delay
            await asyncio.sleep(random.uniform(0.0001, 0.003))

async def suspicious_user(user_id):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
        for _ in range(random.randint(100, 200)):
            endpoint = random.choice(NORMAL_ENDPOINTS + SENSITIVE_ENDPOINTS)

            try:
                await client.get(
                    endpoint,
                    headers=random_headers("suspicious")
                )
            except:
                pass

            # slow but consistent (stealth bot)
            await asyncio.sleep(random.uniform(0.2, 0.6))

async def mixed_attack(user_id):
    """EXTREME: Combined attack pattern"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=3) as client:
        attack_patterns = [
            ("GET", "/api/data"),
            ("POST", "/login"),
            ("GET", "/admin"),
            ("GET", "/config"),
            ("GET", "/.git/config"),
            ("POST", "/reset-password"),
        ]
        
        for _ in range(random.randint(200, 300)):
            method, endpoint = random.choice(attack_patterns)
            
            try:
                if method == "GET":
                    await client.get(endpoint, headers=random_headers("attack"), timeout=2)
                else:
                    await client.post(endpoint, json={"test": "data"}, headers=random_headers("attack"), timeout=2)
            except:
                pass
            
            await asyncio.sleep(random.uniform(0.008, 0.025))

# ============ MAIN SIMULATION ============

async def main():
    print("🔥🔥🔥 EXTREME AGGRESSIVE ATTACK SIMULATION 🔥🔥🔥")
    print("=" * 60)
    print("⚠️  This will generate HIGH risk scores (0.7-0.95)")
    print("=" * 60)
    
    tasks = []
    
    # EXTREME configuration - heavily weighted toward attacks
    user_configs = [
        # Normal users (reduced count for baseline)
        (normal_user, 25, "🟢 Normal Users"),
        
        # EXTREME ATTACKS (increased counts and intensity)
        (aggressive_brute_force, 5, "🔴🔥 Aggressive Brute Force"),
        (aggressive_scanner, 5, "🔴🔥 Aggressive Scanner"),
        (ddos_burst, 8, "🔴🔥 DDoS Burst"),
        (sql_injection_attack, 8, "🔴🔥 SQL Injection"),
        (endpoint_fuzzer, 8, "🔴🔥 Endpoint Fuzzer"),
        (credential_stuffing_aggressive, 8, "🔴🔥 Credential Stuffing"),
        (rapid_fire, 10, "⚡🔥 Rapid Fire"),
        (suspicious_user, 20, "Suspicious Users"),
        (mixed_attack, 8, "🔴🔥 Mixed Attack")
    ]
    
    total_attacks = 0
    for user_func, count, label in user_configs:
        print(f"{label}: {count} instances")
        for i in range(count):
            tasks.append(user_func(i))
            total_attacks += 1
    
    print("=" * 60)
    print(f"💥 Launching {total_attacks} EXTREME attack instances...")
    print("📊 Expected: req_per_min > 100, burst_score > 5, entropy > 2.5")
    print("🎯 Target Risk Score: 0.85 - 0.95 (HIGH/CRITICAL)")
    print("=" * 60)
    
    start = time.time()
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n⚠️ Simulation interrupted by user")
    
    elapsed = time.time() - start
    print(f"\n✅ EXTREME simulation completed in {elapsed:.2f}s")
    print(f"📊 Total attack instances: {total_attacks}")
    print(f"🚀 Estimated requests sent: {total_attacks * 400:,}+")

if __name__ == "__main__":
    asyncio.run(main())