import asyncio
import random
import httpx
import time
from datetime import datetime
from typing import List, Tuple
import signal
import sys

BASE_URL = "http://localhost:8000"

# ============ CONFIGURATION ============
DURATION_MINUTES = 30
NORMAL_USERS_COUNT = 50
SUSPICIOUS_USERS_COUNT = 3
ATTACK_USERS_COUNT = 2

# Large pool of IP addresses to simulate different users
IP_POOL = [
    "192.168.1.101", "192.168.1.102", "192.168.1.103", "192.168.1.104", "192.168.1.105",
    "192.168.1.106", "192.168.1.107", "192.168.1.108", "192.168.1.109", "192.168.1.110",
    "192.168.2.101", "192.168.2.102", "192.168.2.103", "192.168.2.104", "192.168.2.105",
    "10.0.0.101", "10.0.0.102", "10.0.0.103", "10.0.0.104", "10.0.0.105",
    "172.16.0.101", "172.16.0.102", "172.16.0.103", "172.16.0.104", "172.16.0.105",
]

# Realistic User Agents
USER_AGENTS = {
    "browser": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    ],
    "mobile": [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
        "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
    ]
}

# Endpoints
NORMAL_ENDPOINTS = [
    "/api/test",
    "/health", 
    "/api/profile",
    "/api/users/me",
    "/api/products",
    "/api/search",
]

SUSPICIOUS_ENDPOINTS = [
    "/api/data",
    "/api/products", 
    "/api/search",
]

ATTACK_ENDPOINTS = [
    "/login",
    "/admin",
    "/config", 
    "/.env",
    "/debug",
    "/api/private",
]

# ============ IP MANAGEMENT ============
class IPManager:
    def __init__(self):
        self.used_ips = {}
        self.ip_pool = IP_POOL.copy()
        random.shuffle(self.ip_pool)
        self.ip_index = 0
    
    def get_ip_for_user(self, user_id: int) -> str:
        """Assign a consistent IP per user (simulates real user behavior)"""
        if user_id not in self.used_ips:
            # Assign a new IP from pool
            ip = self.ip_pool[self.ip_index % len(self.ip_pool)]
            self.used_ips[user_id] = ip
            self.ip_index += 1
        return self.used_ips[user_id]
    
    def get_rotating_ip(self) -> str:
        """Get random IP for rotating requests (attackers)"""
        return random.choice(self.ip_pool)

ip_manager = IPManager()

# ============ HELPER FUNCTIONS ============
def get_user_agent(user_type: str) -> str:
    if user_type == "normal":
        return random.choice(USER_AGENTS["browser"] + USER_AGENTS["mobile"])
    elif user_type == "suspicious":
        return random.choice(USER_AGENTS["browser"])
    else:
        return random.choice(USER_AGENTS["browser"])

def random_headers(user_type: str, user_id: int, rotate_ip: bool = False) -> dict:
    """Generate headers with consistent or rotating IP"""
    if rotate_ip:
        ip = ip_manager.get_rotating_ip()
    else:
        ip = ip_manager.get_ip_for_user(user_id)
    
    headers = {
        "User-Agent": get_user_agent(user_type),
        "Accept": random.choice(["application/json", "text/html", "*/*"]),
        "Accept-Language": random.choice(["en-US,en;q=0.9", "fr-FR,fr;q=0.8", "de-DE,de;q=0.7"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
    }
    
    if user_type == "attack":
        headers["X-Simulated-Label"] = "attack"
    
    return headers

# ============ USER BEHAVIORS ============

async def normal_user_behavior(user_id: int, stop_event: asyncio.Event):
    """Normal user with consistent IP (simulates real human)"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        session_endpoints = []
        
        while not stop_event.is_set():
            try:
                if len(session_endpoints) < 3 or random.random() < 0.3:
                    session_endpoints = random.sample(NORMAL_ENDPOINTS, min(3, len(NORMAL_ENDPOINTS)))
                
                endpoint = random.choice(session_endpoints)
                
                if endpoint == "/api/search" and random.random() < 0.4:
                    q = random.choice(["laptop", "phone", "tablet", "book"])
                    endpoint = f"/api/search?q={q}"
                
                # Each normal user has their own consistent IP
                headers = random_headers("normal", user_id, rotate_ip=False)
                await client.get(endpoint, headers=headers, timeout=5)
                
                # Human-like delay (1-5 seconds)
                await asyncio.sleep(random.uniform(1.0, 5.0))
                
            except Exception as e:
                await asyncio.sleep(random.uniform(2.0, 4.0))

async def suspicious_user_behavior(user_id: int, stop_event: asyncio.Event):
    """Suspicious user with consistent IP"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        while not stop_event.is_set():
            try:
                if random.random() < 0.7:
                    endpoint = random.choice(NORMAL_ENDPOINTS)
                else:
                    endpoint = random.choice(SUSPICIOUS_ENDPOINTS)
                
                headers = random_headers("suspicious", user_id, rotate_ip=False)
                await client.get(endpoint, headers=headers, timeout=5)
                
                await asyncio.sleep(random.uniform(0.5, 3.0))
                
            except Exception as e:
                await asyncio.sleep(random.uniform(1.0, 2.0))

async def attack_user_behavior(user_id: int, stop_event: asyncio.Event):
    """Attack user - may rotate IPs to avoid detection"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        attack_count = 0
        max_attacks = random.randint(5, 15)
        
        while not stop_event.is_set() and attack_count < max_attacks:
            try:
                attack_type = random.choice(["brute_force", "scanning", "injection"])
                
                if attack_type == "brute_force" and attack_count < max_attacks:
                    passwords = ["admin123", "password123", "123456", "admin", "root"]
                    for pwd in random.sample(passwords, min(3, len(passwords))):
                        # Attackers may rotate IP for each attempt
                        headers = random_headers("attack", user_id, rotate_ip=True)
                        await client.post(
                            "/login",
                            json={"username": "admin", "password": pwd},
                            headers=headers,
                            timeout=3
                        )
                        attack_count += 1
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                
                elif attack_type == "scanning" and attack_count < max_attacks:
                    for endpoint in random.sample(ATTACK_ENDPOINTS, min(3, len(ATTACK_ENDPOINTS))):
                        headers = random_headers("attack", user_id, rotate_ip=True)
                        await client.get(endpoint, headers=headers, timeout=3)
                        attack_count += 1
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                
                elif attack_type == "injection" and attack_count < max_attacks:
                    payloads = ["' OR '1'='1", "admin'--", "1' AND 1=1--"]
                    payload = random.choice(payloads)
                    headers = random_headers("attack", user_id, rotate_ip=True)
                    await client.get(
                        f"/api/search?q={payload}",
                        headers=headers,
                        timeout=3
                    )
                    attack_count += 1
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                
                await asyncio.sleep(random.uniform(2.0, 5.0))
                
            except Exception as e:
                await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # After attacks, behave normally with consistent IP
        await normal_user_behavior(user_id, stop_event)

# ============ MAIN SIMULATION ============

class Simulation:
    def __init__(self):
        self.tasks = []
        self.stop_event = asyncio.Event()
        self.start_time = None
    
    def signal_handler(self, sig, frame):
        print("\n\n🛑 Stopping simulation gracefully...")
        self.stop_event.set()
    
    async def monitor_stats(self):
        while not self.stop_event.is_set():
            elapsed = time.time() - self.start_time
            minutes_remaining = max(0, DURATION_MINUTES - (elapsed / 60))
            
            # Count unique IPs being used
            unique_ips = len(ip_manager.used_ips)
            
            print(f"\r📊 Running: {elapsed/60:.1f}/{DURATION_MINUTES} min | "
                  f"Remaining: {minutes_remaining:.1f} min | "
                  f"Unique IPs: {unique_ips} | "
                  f"Active users: {len(self.tasks)}", end="", flush=True)
            
            await asyncio.sleep(5)
    
    async def run(self):
        print("=" * 70)
        print("🛡️  AI-POWERED API SECURITY SYSTEM - BALANCED SIMULATION")
        print("=" * 70)
        print(f"⏱️  Duration: {DURATION_MINUTES} minutes")
        print(f"🌐 IP Pool Size: {len(IP_POOL)} unique IPs")
        print(f"👥 User Mix:")
        print(f"   ✅ Normal users: {NORMAL_USERS_COUNT} (each with unique IP)")
        print(f"   ⚠️  Suspicious users: {SUSPICIOUS_USERS_COUNT} (each with unique IP)")
        print(f"   🔴 Attack users: {ATTACK_USERS_COUNT} (IP rotation per request)")
        print("=" * 70)
        print("\n🎯 IP Strategy:")
        print("   • Normal users: Consistent IP per user (simulates real humans)")
        print("   • Suspicious: Consistent IP but faster requests")
        print("   • Attackers: Rotating IPs to evade detection")
        print("=" * 70)
        print("\n🚀 Starting simulation... Press Ctrl+C to stop early\n")
        
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.start_time = time.time()
        
        # Create user tasks
        for i in range(NORMAL_USERS_COUNT):
            self.tasks.append(asyncio.create_task(normal_user_behavior(i, self.stop_event)))
        
        for i in range(SUSPICIOUS_USERS_COUNT):
            self.tasks.append(asyncio.create_task(
                suspicious_user_behavior(NORMAL_USERS_COUNT + i, self.stop_event)
            ))
        
        for i in range(ATTACK_USERS_COUNT):
            self.tasks.append(asyncio.create_task(
                attack_user_behavior(NORMAL_USERS_COUNT + SUSPICIOUS_USERS_COUNT + i, self.stop_event)
            ))
        
        monitor_task = asyncio.create_task(self.monitor_stats())
        
        try:
            await asyncio.wait_for(self.stop_event.wait(), timeout=DURATION_MINUTES * 60)
        except asyncio.TimeoutError:
            print("\n\n✅ Simulation completed successfully!")
            self.stop_event.set()
        
        monitor_task.cancel()
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        elapsed = time.time() - self.start_time
        print("\n" + "=" * 70)
        print("📊 SIMULATION COMPLETE")
        print("=" * 70)
        print(f"⏱️  Runtime: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"🌐 Unique IPs used: {len(ip_manager.used_ips)}")
        print(f"👥 Total simulated users: {len(self.tasks)}")
        print("=" * 70)
        print("\n💡 Check your dashboard at http://localhost:3000")
        print("=" * 70)


if __name__ == "__main__":
    simulation = Simulation()
    asyncio.run(simulation.run())