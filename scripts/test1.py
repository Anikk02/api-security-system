import asyncio
import random
import httpx
import time
import math
from collections import defaultdict
from datetime import datetime
import signal

BASE_URL = "http://localhost:8000"

# ============ CONFIGURATION ============
DURATION_MINUTES = 30
NORMAL_USERS_COUNT = 50
SUSPICIOUS_USERS_COUNT = 10
ATTACK_USERS_COUNT = 10

# ============ LARGE, REALISTIC IP POOL ============
# Spread across multiple subnets like a real mixed-traffic environment.
# Corporate/office ranges, residential ISP ranges, mobile/carrier NAT, cloud egress.

def _range(prefix, start, end):
    return [f"{prefix}.{i}" for i in range(start, end + 1)]

IP_POOL = (
    # Corporate LAN – normal office workers
    _range("10.10.1",   1,  60) +
    _range("10.10.2",   1,  60) +
    _range("10.10.3",   1,  40) +

    # Remote/VPN users
    _range("10.20.5",   1,  30) +
    _range("10.20.6",   1,  30) +

    # Residential ISP block A (e.g. Comcast-like)
    _range("74.125.10",  50, 120) +
    _range("74.125.11",  50, 120) +

    # Residential ISP block B (e.g. AT&T-like)
    _range("99.83.140",  1,  80) +
    _range("99.83.141",  1,  80) +

    # Mobile carrier NAT (many users share a few IPs — realistic for 4G/5G)
    _range("100.64.0",   1,  10) +   # carrier-grade NAT range
    _range("100.64.1",   1,  10) +

    # Cloud / SaaS egress (e.g. Slack, Zoom, CDN pops)
    _range("35.190.0",   1,  20) +
    _range("34.102.0",   1,  20) +

    # Suspicious/scanner ranges (used by attack users)
    _range("185.220.101", 1, 30) +   # known Tor exit / scanner range pattern
    _range("45.155.205",  1, 20) +
    _range("194.165.16",  1, 20) +

    # Datacenter IPs (bots, scrapers)
    _range("192.241.200", 1, 30) +
    _range("167.99.200",  1, 30)
)

# ============ REALISTIC USER AGENTS ============
USER_AGENTS = {
    "browser": [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
        # Chrome macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        # Safari macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    ],
    "mobile": [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    ],
    "bot_legit": [
        # Legitimate crawlers (normal traffic)
        "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "Bingbot/2.0; +http://www.bing.com/bingbot.htm",
        "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    ],
    "bot_malicious": [
        "curl/8.5.0",
        "python-httpx/0.27.0",
        "python-requests/2.31.0",
        "Go-http-client/1.1",
        "Scrapy/2.11.0 (+https://scrapy.org)",
        "masscan/1.3 (https://github.com/robertdavidgraham/masscan)",
        "zgrab/0.x",
        "sqlmap/1.8 (https://sqlmap.org)",
    ],
}

# ============ ENDPOINTS ============
NORMAL_ENDPOINTS = [
    ("/api/products",       "GET",  0.30),
    ("/api/search",         "GET",  0.20),
    ("/api/users/me",       "GET",  0.15),
    ("/api/profile",        "GET",  0.10),
    ("/health",             "GET",  0.10),
    ("/api/test",           "GET",  0.08),
    ("/api/orders",         "GET",  0.07),
]

SUSPICIOUS_ENDPOINTS = [
    ("/api/data",           "GET",  0.25),
    ("/api/users",          "GET",  0.20),
    ("/api/admin",          "GET",  0.15),
    ("/api/secure",         "GET",  0.15),
    ("/api/products",       "GET",  0.15),
    ("/api/search",         "GET",  0.10),
]

ATTACK_ENDPOINTS = [
    ("/login",              "POST", 0.25),
    ("/admin",              "GET",  0.15),
    ("/api/admin",          "GET",  0.15),
    ("/.env",               "GET",  0.10),
    ("/config",             "GET",  0.10),
    ("/debug",              "GET",  0.08),
    ("/api/private",        "GET",  0.08),
    ("/reset-password",     "POST", 0.05),
    ("/api/user",           "GET",  0.04),
]

def weighted_choice(options):
    """Pick from (endpoint, method, weight) tuples."""
    endpoints, methods, weights = zip(*options)
    return random.choices(list(zip(endpoints, methods)), weights=weights, k=1)[0]

# ============ IP MANAGER ============
class IPManager:
    def __init__(self):
        self._user_ips: dict[int, str] = {}
        pool = IP_POOL.copy()
        random.shuffle(pool)
        self._pool = pool
        self._idx = 0

        # Pre-split attacker IPs from scanner/datacenter ranges
        self._attacker_pool = (
            _range("185.220.101", 1, 30) +
            _range("45.155.205",  1, 20) +
            _range("194.165.16",  1, 20) +
            _range("192.241.200", 1, 30) +
            _range("167.99.200",  1, 30)
        )

    def get(self, user_id: int) -> str:
        if user_id not in self._user_ips:
            self._user_ips[user_id] = self._pool[self._idx % len(self._pool)]
            self._idx += 1
        return self._user_ips[user_id]

    def rotate(self) -> str:
        """Return a random attacker IP."""
        return random.choice(self._attacker_pool)

    @property
    def unique_count(self):
        return len(self._user_ips)

ip_manager = IPManager()

# ============ HEADER BUILDER ============
def build_headers(user_type: str, user_id: int, rotate_ip: bool = False) -> dict:
    ip = ip_manager.rotate() if rotate_ip else ip_manager.get(user_id)

    if user_type == "normal":
        ua = random.choice(USER_AGENTS["browser"] + USER_AGENTS["mobile"])
    elif user_type == "suspicious":
        ua = random.choice(USER_AGENTS["browser"] + USER_AGENTS["bot_legit"])
    else:
        ua = random.choice(USER_AGENTS["bot_malicious"])

    headers = {
        "User-Agent": ua,
        "Accept": random.choice(["application/json", "text/html,application/xhtml+xml", "*/*"]),
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "fr-FR,fr;q=0.7", "de-DE,de;q=0.8"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
    }

    # Real browsers send Referer and cache headers
    if user_type == "normal":
        headers["Cache-Control"] = random.choice(["no-cache", "max-age=0", ""])
        if random.random() < 0.6:
            headers["Referer"] = f"{BASE_URL}/dashboard"

    if user_type == "attack":
        headers["X-Simulated-Label"] = "attack"

    return headers

# ============ THINK TIME MODELS ============
def human_delay() -> float:
    """Log-normal delay: median ~2s, occasional long pauses (reading content)."""
    return max(0.5, random.lognormvariate(mu=0.7, sigma=0.7))

def bot_delay() -> float:
    """Very short, regular delay — characteristic of automated tools."""
    return random.uniform(0.05, 0.3)

def scanner_delay() -> float:
    """Rapid-fire with brief pauses between bursts."""
    return random.uniform(0.1, 0.5)

# ============ SESSION MODEL ============
class Session:
    """Simulates a user browsing session with realistic page-depth and idle gaps."""

    def __init__(self, user_id: int, endpoints: list, session_depth: int = 5):
        self.user_id = user_id
        self.endpoints = endpoints
        self.depth = session_depth
        self.visited = 0

    def is_done(self) -> bool:
        return self.visited >= self.depth

    def next(self):
        self.visited += 1
        return weighted_choice(self.endpoints)

# ============ USER BEHAVIORS ============

async def normal_user_behavior(user_id: int, stop: asyncio.Event):
    """
    Realistic human:
    - Log-normal inter-request delays
    - Session-based browsing (visits 3–8 pages then idles)
    - Occasional long idle (tab left open, came back)
    - Consistent IP
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        while not stop.is_set():
            # New session: visit 3–8 pages
            depth = random.randint(3, 8)
            session = Session(user_id, NORMAL_ENDPOINTS, depth)

            while not session.is_done() and not stop.is_set():
                endpoint, method = session.next()

                # Append realistic query params
                if "/api/search" in endpoint:
                    q = random.choice(["laptop", "phone", "shoes", "book", "headphones", "chair"])
                    endpoint = f"{endpoint}?q={q}&page={random.randint(1,5)}"
                elif "/api/products" in endpoint and random.random() < 0.4:
                    endpoint = f"{endpoint}?category={random.choice(['electronics','clothing','home'])}"

                headers = build_headers("normal", user_id)
                try:
                    await client.request(method, endpoint, headers=headers, timeout=5)
                except Exception:
                    pass

                await asyncio.sleep(human_delay())

            # Session idle gap (user reads content, switches tabs, etc.)
            if not stop.is_set():
                await asyncio.sleep(random.uniform(5.0, 30.0))


async def suspicious_user_behavior(user_id: int, stop: asyncio.Event):
    """
    Suspicious:
    - Faster than human, no long idles
    - Mixes normal + sensitive endpoints
    - Occasionally probes endpoints not in normal flow
    - Consistent IP (not rotating)
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        while not stop.is_set():
            # 65% normal, 35% suspicious endpoint
            pool = NORMAL_ENDPOINTS if random.random() < 0.65 else SUSPICIOUS_ENDPOINTS
            endpoint, method = weighted_choice(pool)

            if "/api/search" in endpoint:
                # Suspicious: tries many different search terms quickly
                endpoint = f"{endpoint}?q={random.choice(['admin','config','password','user','token','key'])}"

            headers = build_headers("suspicious", user_id)
            try:
                await client.request(method, endpoint, headers=headers, timeout=5)
            except Exception:
                pass

            # Faster than human, no long pauses
            await asyncio.sleep(random.uniform(0.3, 2.0))


async def attack_user_behavior(user_id: int, stop: asyncio.Event):
    """
    Attacker:
    - Rotates IPs per request
    - Uses malicious UAs
    - Runs distinct attack phases: brute-force, scanning, injection
    - After attack budget exhausted → blends into normal to avoid detection
    """
    attack_budget = random.randint(20, 50)
    used = 0

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:

        # --- Phase 1: Recon scan ---
        recon_targets = ["/.env", "/debug", "/config", "/admin", "/api/admin", "/api/private"]
        random.shuffle(recon_targets)
        for target in recon_targets[:random.randint(2, 5)]:
            if stop.is_set() or used >= attack_budget:
                break
            headers = build_headers("attack", user_id, rotate_ip=True)
            try:
                await client.get(target, headers=headers, timeout=3)
            except Exception:
                pass
            used += 1
            await asyncio.sleep(scanner_delay())

        # --- Phase 2: Credential stuffing / brute force ---
        credentials = [
            ("admin",  ["admin123", "password", "Admin@123", "123456", "admin"]),
            ("root",   ["root", "toor", "password123", "root123"]),
            ("user",   ["user123", "welcome1", "password"]),
        ]
        for username, passwords in random.sample(credentials, k=random.randint(1, 2)):
            for pwd in random.sample(passwords, k=min(3, len(passwords))):
                if stop.is_set() or used >= attack_budget:
                    break
                headers = build_headers("attack", user_id, rotate_ip=True)
                try:
                    await client.post(
                        "/login",
                        json={"username": username, "password": pwd},
                        headers=headers,
                        timeout=3
                    )
                except Exception:
                    pass
                used += 1
                await asyncio.sleep(random.uniform(0.2, 0.8))

        # --- Phase 3: Injection attempts ---
        sql_payloads = [
            "' OR '1'='1",
            "admin'--",
            "1; DROP TABLE users--",
            "' UNION SELECT null,null,null--",
            "1' AND SLEEP(5)--",
        ]
        xss_payloads = [
            "<script>alert(1)</script>",
            "javascript:alert(document.cookie)",
            "\"><img src=x onerror=alert(1)>",
        ]
        path_payloads = ["../../../etc/passwd", "..%2F..%2F..%2Fetc%2Fshadow"]

        all_payloads = sql_payloads + xss_payloads + path_payloads
        for payload in random.sample(all_payloads, k=min(5, attack_budget - used)):
            if stop.is_set() or used >= attack_budget:
                break
            endpoint = random.choice([
                f"/api/search?q={payload}",
                f"/api/data?id={payload}",
                f"/api/users/{payload}",
            ])
            headers = build_headers("attack", user_id, rotate_ip=True)
            try:
                await client.get(endpoint, headers=headers, timeout=3)
            except Exception:
                pass
            used += 1
            await asyncio.sleep(scanner_delay())

    # --- Phase 4: Blend in (evade detection) ---
    # After attack budget spent, switch to normal-looking behavior
    await normal_user_behavior(user_id, stop)


# ============ MAIN SIMULATION ============

class Simulation:
    def __init__(self):
        self.tasks: list[asyncio.Task] = []
        self.stop_event = asyncio.Event()
        self.start_time: float = 0

    def _signal_handler(self, sig, frame):
        print("\n\n🛑 Stopping simulation gracefully...")
        self.stop_event.set()

    async def _monitor(self):
        while not self.stop_event.is_set():
            elapsed = time.time() - self.start_time
            remaining = max(0, DURATION_MINUTES * 60 - elapsed)
            print(
                f"\r📊 {elapsed/60:.1f}/{DURATION_MINUTES} min | "
                f"Remaining: {remaining/60:.1f} min | "
                f"Unique IPs: {ip_manager.unique_count} | "
                f"Active tasks: {sum(1 for t in self.tasks if not t.done())}",
                end="", flush=True
            )
            await asyncio.sleep(5)

    async def run(self):
        print("=" * 70)
        print("🛡️  AI-POWERED API SECURITY SYSTEM — REALISTIC SIMULATION")
        print("=" * 70)
        print(f"⏱️  Duration      : {DURATION_MINUTES} minutes")
        print(f"🌐 IP Pool Size  : {len(IP_POOL)} unique IPs across 12 subnets")
        print(f"👥 User Mix:")
        print(f"   ✅ Normal users    : {NORMAL_USERS_COUNT}  (log-normal delays, session model)")
        print(f"   ⚠️  Suspicious users: {SUSPICIOUS_USERS_COUNT}  (fast, mixed endpoints)")
        print(f"   🔴 Attack users    : {ATTACK_USERS_COUNT}  (recon → brute-force → injection → blend-in)")
        print("=" * 70)

        signal.signal(signal.SIGINT, self._signal_handler)
        self.start_time = time.time()

        for i in range(NORMAL_USERS_COUNT):
            self.tasks.append(asyncio.create_task(
                normal_user_behavior(i, self.stop_event)
            ))

        for i in range(SUSPICIOUS_USERS_COUNT):
            self.tasks.append(asyncio.create_task(
                suspicious_user_behavior(NORMAL_USERS_COUNT + i, self.stop_event)
            ))

        for i in range(ATTACK_USERS_COUNT):
            self.tasks.append(asyncio.create_task(
                attack_user_behavior(NORMAL_USERS_COUNT + SUSPICIOUS_USERS_COUNT + i, self.stop_event)
            ))

        monitor = asyncio.create_task(self._monitor())

        try:
            await asyncio.wait_for(self.stop_event.wait(), timeout=DURATION_MINUTES * 60)
        except asyncio.TimeoutError:
            print("\n\n✅ Simulation completed!")
            self.stop_event.set()

        monitor.cancel()
        for t in self.tasks:
            t.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

        elapsed = time.time() - self.start_time
        print("\n" + "=" * 70)
        print("📊 SIMULATION COMPLETE")
        print(f"⏱️  Runtime       : {elapsed:.0f}s ({elapsed/60:.1f} min)")
        print(f"🌐 Unique IPs    : {ip_manager.unique_count}")
        print(f"👥 Total users   : {len(self.tasks)}")
        print("=" * 70)
        print("💡 Dashboard → http://localhost:3000")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(Simulation().run())