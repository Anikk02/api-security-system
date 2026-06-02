import asyncio
import random
import httpx
import time
import signal
from collections import defaultdict
from datetime import datetime
import uuid

# ============ CONFIGURATION ============
BASE_URL = "http://localhost:8000"
DURATION_MINUTES = 10  # Run for 10 minutes

# ============ REAL IP POOL WITH GEO LOCATIONS ============
# IPs mapped to realistic geographic regions for threat map
IP_GEO_MAPPING = {
    # North America (Suspicious)
    "45.155.205.10": "North America", "45.155.205.11": "North America",
    "45.155.205.12": "North America", "45.155.205.13": "North America",
    # Europe (Suspicious)
    "185.220.101.5": "Europe", "185.220.101.6": "Europe",
    "185.220.101.7": "Europe", "185.220.101.8": "Europe",
    # Asia (Suspicious)
    "194.165.16.20": "Asia", "194.165.16.21": "Asia",
    "194.165.16.22": "Asia", "194.165.16.23": "Asia",
    # South America (Suspicious)
    "167.99.200.75": "South America", "167.99.200.76": "South America",
    # Normal user IPs
    "192.168.1.101": "North America", "192.168.1.102": "North America",
    "192.168.1.103": "Europe", "192.168.2.101": "Asia",
    "10.0.0.101": "North America", "172.16.1.101": "Europe",
}

NORMAL_IPS = ["192.168.1.101", "192.168.1.102", "192.168.1.103", 
              "192.168.2.101", "10.0.0.101", "172.16.1.101"]
SUSPICIOUS_IPS = ["45.155.205.10", "45.155.205.11", "185.220.101.5", 
                  "185.220.101.6", "194.165.16.20", "167.99.200.75"]

# ============ USER AGENTS ============
USER_AGENTS = {
    "normal": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) Version/17.4 Mobile/15E148 Safari/604.1",
    ],
    "attack": [
        "curl/8.5.0", "python-httpx/0.27.0", "sqlmap/1.8", "masscan/1.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    ]
}

# ============ ENDPOINTS ============
NORMAL_ENDPOINTS = [
    "/api/test", "/health", "/api/products", "/api/search",
    "/api/users/me", "/api/profile", "/api/orders", "/api/cart",
]

SUSPICIOUS_ENDPOINTS = [
    "/api/data", "/api/admin/users", "/api/internal/metrics",
    "/admin/dashboard", "/api/private", "/api/internal",
]

ATTACK_ENDPOINTS = [
    "/.env", "/debug", "/config", "/.git/config", "/backup/db.sql",
    "/phpmyadmin", "/graphql", "/api/admin", "/login", "/auth",
]

# ============ ATTACK PAYLOADS ============
SQL_PAYLOADS = [
    "' OR '1'='1", "' OR 1=1--", "admin'--", "1' AND SLEEP(5)--",
]

XSS_PAYLOADS = [
    "<script>alert(1)</script>", "<img src=x onerror=alert(1)>",
]

# ============ REQUEST STATS ============
class RequestStats:
    def __init__(self):
        self.total = 0
        self.normal = 0
        self.attack = 0
        self.suspicious = 0
        self.violations = 0
        self.start_time = time.time()
        self.attack_sources = defaultdict(int)  # Track attack IPs by region

    def log(self, user_type: str, ip: str, is_violation: bool = False):
        self.total += 1
        if user_type == "normal":
            self.normal += 1
        elif user_type == "attack":
            self.attack += 1
        else:
            self.suspicious += 1
        
        if is_violation:
            self.violations += 1
            region = IP_GEO_MAPPING.get(ip, "Unknown")
            self.attack_sources[region] += 1

    def report(self):
        elapsed = time.time() - self.start_time
        return {
            "total": self.total,
            "rate": self.total / elapsed if elapsed > 0 else 0,
            "normal": self.normal,
            "attack": self.attack,
            "suspicious": self.suspicious,
            "violations": self.violations,
            "attack_sources": dict(self.attack_sources),
        }

stats = RequestStats()

# ============ REQUEST FUNCTION ============
async def make_request(client: httpx.AsyncClient, method: str, endpoint: str, 
                       user_type: str, ip: str, json_data: dict = None):
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS[user_type] if user_type in USER_AGENTS else USER_AGENTS["normal"]),
        "Accept": "application/json",
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
    }
    
    # Add random query params for search endpoints
    if "/api/search" in endpoint and method == "GET":
        if user_type == "attack":
            payload = random.choice(SQL_PAYLOADS + XSS_PAYLOADS)
            endpoint = f"{endpoint}?q={payload}"
        else:
            endpoint = f"{endpoint}?q={random.choice(['laptop','phone','shoes'])}"
    
    try:
        if json_data:
            response = await client.request(method, endpoint, json=json_data, headers=headers, timeout=10)
        else:
            response = await client.request(method, endpoint, headers=headers, timeout=10)
        
        # Consider 4xx/5xx as potential violations for attack traffic
        is_violation = (user_type in ["attack", "suspicious"] and response.status_code >= 400)
        stats.log(user_type, ip, is_violation)
        
        return response
    except Exception:
        stats.log(user_type, ip, True)
        return None

# ============ USER BEHAVIORS ============

async def normal_user(user_id: int, stop: asyncio.Event):
    """Normal user - regular API usage"""
    ip = random.choice(NORMAL_IPS)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
        while not stop.is_set():
            endpoint = random.choice(NORMAL_ENDPOINTS)
            await make_request(client, "GET", endpoint, "normal", ip)
            await asyncio.sleep(random.uniform(1, 4))

async def suspicious_user(user_id: int, stop: asyncio.Event):
    """Suspicious user - probes sensitive endpoints"""
    ip = random.choice(SUSPICIOUS_IPS)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        while not stop.is_set():
            endpoint = random.choice(SUSPICIOUS_ENDPOINTS)
            await make_request(client, "GET", endpoint, "suspicious", ip)
            await asyncio.sleep(random.uniform(0.5, 2))

async def attack_user(user_id: int, stop: asyncio.Event):
    """Attack user - credential stuffing and scanning"""
    # Attackers rotate IPs
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=8) as client:
        while not stop.is_set():
            ip = random.choice(SUSPICIOUS_IPS)
            
            # 70% attack endpoints, 30% normal (to blend in)
            if random.random() < 0.7:
                endpoint = random.choice(ATTACK_ENDPOINTS)
                method = "POST" if "/login" in endpoint or "/auth" in endpoint else "GET"
                
                if method == "POST":
                    credentials = {
                        "username": random.choice(["admin", "root", "user"]),
                        "password": random.choice(["admin123", "password", "123456", "admin"])
                    }
                    await make_request(client, method, endpoint, "attack", ip, json_data=credentials)
                else:
                    await make_request(client, method, endpoint, "attack", ip)
            else:
                endpoint = random.choice(NORMAL_ENDPOINTS)
                await make_request(client, "GET", endpoint, "attack", ip)
            
            await asyncio.sleep(random.uniform(0.1, 0.8))

async def injection_user(user_id: int, stop: asyncio.Event):
    """SQL Injection and XSS attacks"""
    ip = random.choice(SUSPICIOUS_IPS)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        while not stop.is_set():
            attack_type = random.choice(["sql", "xss"])
            
            if attack_type == "sql":
                payload = random.choice(SQL_PAYLOADS)
                endpoint = f"/api/search?q={payload}"
            else:
                payload = random.choice(XSS_PAYLOADS)
                endpoint = f"/api/search?q={payload}"
            
            await make_request(client, "GET", endpoint, "attack", ip)
            await asyncio.sleep(random.uniform(0.2, 1.0))

# ============ STATS MONITOR ============
async def stats_reporter(stop: asyncio.Event):
    """Report statistics periodically"""
    last_total = 0
    while not stop.is_set():
        await asyncio.sleep(5)
        report = stats.report()
        rate = (report['total'] - last_total) / 5
        last_total = report['total']
        
        # Calculate violation rate
        violation_rate = (report['violations'] / report['total'] * 100) if report['total'] > 0 else 0
        
        print(f"\r📊 {report['total']} reqs | {rate:.1f} req/s | "
              f"Normal: {report['normal']} | Attack: {report['attack']} | "
              f"⚠️ Violations: {report['violations']} ({violation_rate:.1f}%)    ", 
              end="", flush=True)

# ============ SIMULATION ============
class Simulation:
    def __init__(self):
        self.tasks = []
        self.stop_event = asyncio.Event()

    def _signal_handler(self, sig, frame):
        print("\n\n🛑 Stopping simulation...")
        self.stop_event.set()

    async def run(self):
        print("=" * 70)
        print("🛡️  API SECURITY TEST - REALISTIC TRAFFIC")
        print("=" * 70)
        print(f"🎯 Target: {BASE_URL}")
        print(f"⏱️  Duration: {DURATION_MINUTES} minutes")
        print(f"\n👥 Simulated Users:")
        print(f"   ✅ Normal users: 20")
        print(f"   ⚠️  Suspicious: 5")
        print(f"   🔴 Attack users: 8")
        print(f"   💉 Injection: 4")
        print(f"\n🌍 Attack Sources: US, Europe, Asia, South America")
        print("=" * 70)
        print("\n🚀 Starting traffic generation...\n")
        
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Create user tasks
        user_id = 0
        for _ in range(20):  # 20 normal users
            self.tasks.append(asyncio.create_task(normal_user(user_id, self.stop_event)))
            user_id += 1
        
        for _ in range(5):  # 5 suspicious users
            self.tasks.append(asyncio.create_task(suspicious_user(user_id, self.stop_event)))
            user_id += 1
        
        for _ in range(8):  # 8 attack users
            self.tasks.append(asyncio.create_task(attack_user(user_id, self.stop_event)))
            user_id += 1
        
        for _ in range(4):  # 4 injection users
            self.tasks.append(asyncio.create_task(injection_user(user_id, self.stop_event)))
            user_id += 1
        
        # Stats reporter
        self.tasks.append(asyncio.create_task(stats_reporter(self.stop_event)))
        
        try:
            await asyncio.wait_for(self.stop_event.wait(), timeout=DURATION_MINUTES * 60)
        except asyncio.TimeoutError:
            print("\n\n✅ Test completed!")
            self.stop_event.set()
        
        # Cleanup
        for t in self.tasks:
            t.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Final report
        report = stats.report()
        elapsed = time.time() - stats.start_time
        
        print("\n\n" + "=" * 70)
        print("📊 FINAL REPORT")
        print("=" * 70)
        print(f"⏱️  Runtime: {elapsed:.0f}s ({elapsed/60:.1f} min)")
        print(f"📡 Total requests: {report['total']}")
        print(f"📈 Avg rate: {report['rate']:.1f} req/s")
        print(f"\n📊 Traffic Breakdown:")
        print(f"   ✅ Normal: {report['normal']} ({report['normal']/report['total']*100:.1f}%)")
        print(f"   ⚠️  Suspicious: {report['suspicious']} ({report['suspicious']/report['total']*100:.1f}%)")
        print(f"   🔴 Attack: {report['attack']} ({report['attack']/report['total']*100:.1f}%)")
        print(f"\n⚠️  Violations detected: {report['violations']}")
        print(f"   Violation rate: {report['violations']/report['total']*100:.1f}%")
        print(f"\n🌍 Attack Sources (for Threat Map):")
        for region, count in report['attack_sources'].items():
            print(f"   - {region}: {count} violations")
        print("=" * 70)
        print("\n💡 Your dashboard should now show:")
        print(f"   - Violations Detected: ~{report['violations']}")
        print(f"   - Suspicious Sessions: ~{report['attack'] + report['suspicious']}")
        print(f"   - Requests Per Second: ~{report['rate']:.1f}")
        print(f"   - Threat Map: Activity from {len(report['attack_sources'])} regions")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(Simulation().run())