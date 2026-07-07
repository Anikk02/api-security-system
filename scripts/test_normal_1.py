#!/usr/bin/env python3
"""
Enhanced test script for API security system with realistic traffic patterns.
Uses CONSISTENT IPs per user with occasional realistic IP changes.
This allows proper user tracking and security system testing.
"""

import requests
import random
import time
import uuid
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import Counter, defaultdict
from datetime import datetime
import json

BASE_URL = "http://localhost:8000"

# ============ CONFIGURATION ============
DURATION_MINUTES = 30
NORMAL_USERS_COUNT = 50
SUSPICIOUS_USERS_COUNT = 10
ATTACK_USERS_COUNT = 10

# 🔑 API Key for authentication
API_KEY = ""

# ============ IP POOL ============
IP_POOL = [
    # Home users
    f"192.168.1.{i}" for i in range(101, 200)
] + [
    # Corporate users  
    f"10.0.0.{i}" for i in range(101, 200)
] + [
    # Datacenter
    f"172.16.0.{i}" for i in range(101, 200)
] + [
    # More diverse IPs
    f"192.168.2.{i}" for i in range(101, 150)
]

# ============ ENHANCED USER AGENTS ============
USER_AGENTS = {
    "browser": [
        # Chrome - Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        # Chrome - Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Firefox - Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        # Firefox - Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        # Safari - Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        # Edge - Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ],
    "mobile": [
        # iPhone
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        # Samsung Android
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
        # Google Pixel
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    ],
    "bot": [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
    ]
}

# ============ ENDPOINTS ============
NORMAL_ENDPOINTS = [
    "/api/profile",
    "/api/users/me",
    "/api/products",
    "/api/search",
    "/api/feed",
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

# ============ USER BEHAVIOR CONFIGURATION ============
USER_BEHAVIORS = {
    "normal": {
        "delay_range": (1.0, 5.0),
        "ip_rotation": False,
        "error_rate": 0.02,
        "ip_change_interval": (300, 1800),  # 5-30 minutes between IP changes
        "ip_change_probability": 0.3,  # 30% chance to change IP when interval elapses
    },
    "suspicious": {
        "delay_range": (0.5, 3.0),
        "ip_rotation": False,
        "error_rate": 0.05,
        "ip_change_interval": (600, 3600),  # 10-60 minutes
        "ip_change_probability": 0.1,  # 10% chance
    },
    "attack": {
        "delay_range": (0.1, 1.0),
        "ip_rotation": True,
        "error_rate": 0.10,
        "ip_change_interval": (1, 5),  # 1-5 seconds for attackers
        "ip_change_probability": 1.0,  # Always change IP
    }
}

# ============ IP MANAGER WITH PERSISTENT IPs ============
class IPManager:
    def __init__(self):
        self.used_ips = {}  # user_id -> current_ip
        self.ip_history = {}  # user_id -> list of IPs used
        self.ip_change_timers = {}  # user_id -> next change timestamp
        self.ip_pool = IP_POOL.copy()
        random.shuffle(self.ip_pool)
        self.ip_index = 0
    
    def get_ip_for_user(self, user_id: int, user_type: str = "normal") -> str:
        """Get consistent IP for a user with occasional changes"""
        behavior = USER_BEHAVIORS.get(user_type, USER_BEHAVIORS["normal"])
        
        # Attackers always get rotating IPs
        if user_type == "attack":
            return self.get_rotating_ip()
        
        # First time - assign a new IP
        if user_id not in self.used_ips:
            ip = self.ip_pool[self.ip_index % len(self.ip_pool)]
            self.used_ips[user_id] = ip
            self.ip_history[user_id] = [ip]
            self.ip_index += 1
            
            # Set timer for next IP change
            min_interval, max_interval = behavior["ip_change_interval"]
            self.ip_change_timers[user_id] = time.time() + random.uniform(min_interval, max_interval)
            return ip
        
        # Check if it's time to change IP
        current_time = time.time()
        if current_time > self.ip_change_timers.get(user_id, 0):
            # Check probability of changing IP
            if random.random() < behavior["ip_change_probability"]:
                old_ip = self.used_ips[user_id]
                # Try to get a new IP
                attempts = 0
                while attempts < 10:
                    new_ip = random.choice(self.ip_pool)
                    if new_ip != old_ip:
                        self.used_ips[user_id] = new_ip
                        self.ip_history[user_id].append(new_ip)
                        
                        # Reset timer
                        min_interval, max_interval = behavior["ip_change_interval"]
                        self.ip_change_timers[user_id] = time.time() + random.uniform(min_interval, max_interval)
                        break
                    attempts += 1
        
        return self.used_ips.get(user_id, self.ip_pool[0])
    
    def get_rotating_ip(self) -> str:
        """Get random IP for attackers"""
        return random.choice(self.ip_pool)
    
    def get_ip_history(self, user_id: int) -> list:
        """Get IP history for a user"""
        return self.ip_history.get(user_id, [])
    
    def get_stats(self) -> dict:
        """Get IP manager statistics"""
        total_changes = sum(len(history) - 1 for history in self.ip_history.values() if len(history) > 1)
        return {
            "unique_users": len(self.used_ips),
            "total_ips_used": len(self.ip_pool),
            "ip_changes": total_changes,
            "users_with_changes": sum(1 for h in self.ip_history.values() if len(h) > 1)
        }

ip_manager = IPManager()

# ============ HELPER FUNCTIONS ============
def get_user_agent(user_type: str) -> str:
    """Get realistic user agent based on user type"""
    if user_type == "normal":
        return random.choice(USER_AGENTS["browser"] + USER_AGENTS["mobile"])
    elif user_type == "suspicious":
        return random.choice(USER_AGENTS["browser"])
    else:
        return random.choice(USER_AGENTS["browser"] + USER_AGENTS["bot"])

def random_headers(user_type: str, user_id: int, rotate_ip: bool = False) -> dict:
    """Generate headers with consistent or rotating IP"""
    if rotate_ip or user_type == "attack":
        ip = ip_manager.get_rotating_ip()
    else:
        ip = ip_manager.get_ip_for_user(user_id, user_type)
    
    headers = {
        "X-API-KEY": API_KEY,  # 🔑 Authentication
        "User-Agent": get_user_agent(user_type),
        "Accept": random.choice(["application/json", "text/html", "*/*"]),
        "Accept-Language": random.choice(["en-US,en;q=0.9", "fr-FR,fr;q=0.8", "de-DE,de;q=0.7"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
        "X-Simulated-User-Type": user_type,
        "X-Simulated-User-ID": str(user_id),
    }
    
    if user_type == "attack":
        headers["X-Simulated-Label"] = "attack"
    
    return headers

# ============ USER BEHAVIORS ============

def normal_user_behavior(user_id: int, stop_event: threading.Event):
    """Normal user with consistent IP and occasional changes"""
    session_endpoints = []
    request_count = 0
    
    while not stop_event.is_set():
        try:
            # Rotate endpoints occasionally
            if len(session_endpoints) < 3 or random.random() < 0.3:
                session_endpoints = random.sample(NORMAL_ENDPOINTS, min(3, len(NORMAL_ENDPOINTS)))
            
            endpoint = random.choice(session_endpoints)
            
            if endpoint == "/api/search" and random.random() < 0.4:
                search_terms = ["laptop", "phone", "tablet", "book", "monitor", "keyboard"]
                q = random.choice(search_terms)
                endpoint = f"/api/search?q={q}"
            
            # Get consistent IP (with occasional changes)
            headers = random_headers("normal", user_id, rotate_ip=False)
            ip = headers.get("X-Forwarded-For")
            
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            request_count += 1
            
            if response.status_code == 429:
                print(f"\n⚠️  Rate limited: Normal User {user_id} at {endpoint} (IP: {ip})")
            
            # Human-like delay
            time.sleep(random.uniform(*USER_BEHAVIORS["normal"]["delay_range"]))
            
        except Exception as e:
            time.sleep(random.uniform(1.0, 3.0))

def suspicious_user_behavior(user_id: int, stop_event: threading.Event):
    """Suspicious user with consistent IP but faster requests"""
    request_count = 0
    
    while not stop_event.is_set():
        try:
            if random.random() < 0.7:
                endpoint = random.choice(NORMAL_ENDPOINTS)
            else:
                endpoint = random.choice(SUSPICIOUS_ENDPOINTS)
            
            headers = random_headers("suspicious", user_id, rotate_ip=False)
            ip = headers.get("X-Forwarded-For")
            
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            request_count += 1
            
            if response.status_code == 429:
                print(f"\n⚠️  Suspicious user {user_id} rate limited at {endpoint} (IP: {ip})")
            
            time.sleep(random.uniform(*USER_BEHAVIORS["suspicious"]["delay_range"]))
            
        except Exception as e:
            time.sleep(random.uniform(0.5, 1.5))

def attack_user_behavior(user_id: int, stop_event: threading.Event):
    """Attack user with rotating IPs"""
    attack_count = 0
    max_attacks = random.randint(5, 15)
    
    while not stop_event.is_set() and attack_count < max_attacks:
        try:
            attack_type = random.choice(["brute_force", "scanning", "injection"])
            
            if attack_type == "brute_force":
                passwords = ["admin123", "password123", "123456", "admin", "root"]
                for pwd in random.sample(passwords, min(2, len(passwords))):
                    headers = random_headers("attack", user_id, rotate_ip=True)
                    response = requests.post(
                        f"{BASE_URL}/login",
                        json={"username": "admin", "password": pwd},
                        headers=headers,
                        timeout=3
                    )
                    attack_count += 1
                    if attack_count % 2 == 0:
                        print(f"\n🔴 Attack {attack_count}/{max_attacks}: Brute force attempt")
                    time.sleep(random.uniform(0.3, 0.8))
            
            elif attack_type == "scanning":
                for endpoint in random.sample(ATTACK_ENDPOINTS, min(2, len(ATTACK_ENDPOINTS))):
                    headers = random_headers("attack", user_id, rotate_ip=True)
                    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=3)
                    attack_count += 1
                    if attack_count % 2 == 0:
                        print(f"\n🔴 Attack {attack_count}/{max_attacks}: Scanning {endpoint}")
                    time.sleep(random.uniform(0.2, 0.5))
            
            elif attack_type == "injection":
                payloads = ["' OR '1'='1", "admin'--", "1' AND 1=1--"]
                payload = random.choice(payloads)
                headers = random_headers("attack", user_id, rotate_ip=True)
                response = requests.get(
                    f"{BASE_URL}/api/search?q={payload}",
                    headers=headers,
                    timeout=3
                )
                attack_count += 1
                if attack_count % 2 == 0:
                    print(f"\n🔴 Attack {attack_count}/{max_attacks}: SQL injection attempt")
                time.sleep(random.uniform(0.5, 1.0))
            
            time.sleep(random.uniform(1.0, 3.0))
            
        except Exception as e:
            time.sleep(random.uniform(1.0, 2.0))
    
    # After attacks, behave normally with consistent IP
    if attack_count >= max_attacks:
        print(f"\n✅ Attack user {user_id} completed {attack_count} attacks, now behaving normally")
        normal_user_behavior(user_id, stop_event)

# ============ MAIN SIMULATION ============

class Simulation:
    def __init__(self):
        self.threads = []
        self.stop_event = threading.Event()
        self.start_time = None
    
    def signal_handler(self, sig, frame):
        print("\n\n🛑 Stopping simulation gracefully...")
        self.stop_event.set()
    
    def run(self):
        import signal
        print("=" * 80)
        print("🛡️  API SECURITY SYSTEM - REALISTIC TRAFFIC SIMULATION")
        print("=" * 80)
        print(f"⏱️  Duration: {DURATION_MINUTES} minutes")
        print(f"🔑 API Key: {API_KEY[:20]}... (authenticated)")
        print(f"🌐 IP Pool Size: {len(IP_POOL)} unique IPs")
        print(f"👥 User Mix:")
        print(f"   ✅ Normal users: {NORMAL_USERS_COUNT} (consistent IP with occasional changes)")
        print(f"   ⚠️  Suspicious users: {SUSPICIOUS_USERS_COUNT} (consistent IP, faster requests)")
        print(f"   🔴 Attack users: {ATTACK_USERS_COUNT} (rotating IPs)")
        print("=" * 80)
        print("\n🎯 IP Strategy:")
        print("   • Normal users: Consistent IP per user (occasional IP changes)")
        print("   • Suspicious: Consistent IP but faster requests")
        print("   • Attackers: Rotating IPs to evade detection")
        print("=" * 80)
        print("\n🚀 Starting simulation... Press Ctrl+C to stop early\n")
        
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.start_time = time.time()
        
        # Create user threads
        user_id = 0
        
        # Normal users
        for i in range(NORMAL_USERS_COUNT):
            thread = threading.Thread(target=normal_user_behavior, args=(user_id + i, self.stop_event))
            thread.daemon = True
            self.threads.append(thread)
        user_id += NORMAL_USERS_COUNT
        
        # Suspicious users
        for i in range(SUSPICIOUS_USERS_COUNT):
            thread = threading.Thread(target=suspicious_user_behavior, args=(user_id + i, self.stop_event))
            thread.daemon = True
            self.threads.append(thread)
        user_id += SUSPICIOUS_USERS_COUNT
        
        # Attack users
        for i in range(ATTACK_USERS_COUNT):
            thread = threading.Thread(target=attack_user_behavior, args=(user_id + i, self.stop_event))
            thread.daemon = True
            self.threads.append(thread)
        
        # Start all threads
        for thread in self.threads:
            thread.start()
        
        # Monitor stats
        try:
            while not self.stop_event.is_set():
                elapsed = time.time() - self.start_time
                minutes_remaining = max(0, DURATION_MINUTES - (elapsed / 60))
                ip_stats = ip_manager.get_stats()
                
                print(f"\r📊 Running: {elapsed/60:.1f}/{DURATION_MINUTES} min | "
                      f"Remaining: {minutes_remaining:.1f} min | "
                      f"Unique Users: {ip_stats['unique_users']} | "
                      f"IP Changes: {ip_stats['ip_changes']} | "
                      f"Active users: {len(self.threads)}", end="", flush=True)
                
                time.sleep(5)
        except KeyboardInterrupt:
            self.stop_event.set()
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=1)
        
        elapsed = time.time() - self.start_time
        ip_stats = ip_manager.get_stats()
        
        print("\n" + "=" * 80)
        print("📊 SIMULATION COMPLETE")
        print("=" * 80)
        print(f"⏱️  Runtime: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"👥 Total simulated users: {len(self.threads)}")
        print(f"🌐 Unique users tracked: {ip_stats['unique_users']}")
        print(f"🔄 IP changes: {ip_stats['ip_changes']}")
        print(f"📈 Users with IP changes: {ip_stats['users_with_changes']}")
        print("=" * 80)
        print("\n💡 Check your dashboard at http://localhost:3000")
        print("📋 Expected Dashboard Behavior:")
        print("   • Normal users: Show consistent identity with occasional IP changes")
        print("   • Suspicious users: Higher risk scores, consistent identity")
        print("   • Attack users: Multiple IPs for same identity (IP rotation detected)")
        print("=" * 80)


def health_check():
    """Check if server is running"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        if resp.status_code == 200:
            print("✅ Server is healthy")
            return True
    except:
        pass
    
    print("❌ Server is not running on port 8000")
    return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("API SECURITY SYSTEM - REALISTIC TRAFFIC TEST")
    print("=" * 60)
    print(f"🔑 API Key: {API_KEY[:20]}...")
    print("=" * 60)
    
    if health_check():
        simulation = Simulation()
        simulation.run()
        print("\n✅ Test completed! All requests were authenticated with the API key.")
        print("   Each user has a consistent IP with occasional realistic changes.")
    else:
        print("\n❌ Start your API server first:")
        print("   cd C:\\edb\\api_security_system")
        print("   python -m app.main")