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
NORMAL_USERS_COUNT = 100
SUSPICIOUS_USERS_COUNT = 15
ATTACK_USERS_COUNT = 12

# 🔑 API Key for authentication
API_KEY = ""

# ============ IP POOL ============
IP_POOL = {
    "home": [f"192.168.1.{i}" for i in range(101, 200)],
    "corporate": [f"10.0.0.{i}" for i in range(101, 200)],
    "datacenter": [f"172.16.0.{i}" for i in range(101, 200)],
    "mobile": [f"172.16.1.{i}" for i in range(101, 150)],
    "public": [f"192.168.2.{i}" for i in range(101, 150)],
    "vpn": [f"192.168.3.{i}" for i in range(101, 120)],
}

# Flatten for random access
ALL_IPS = []
for ips in IP_POOL.values():
    ALL_IPS.extend(ips)

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
        "Mozilla/5.0 (compatible; DuckDuckBot/1.0; +https://duckduckgo.com/duckduckbot)",
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
        "error_rate": 0.02,
        "ip_change_interval": (60, 300),  # 1-5 minutes between IP changes
        "ip_change_probability": 0.4,  # 40% chance to change IP when interval elapses
        "session_duration": (120, 600),  # 2-10 minutes per session
        "user_agent_rotation": 0.1,  # 10% chance to change user agent
        "device_types": ["browser", "mobile"],
    },
    "suspicious": {
        "delay_range": (0.5, 3.0),
        "error_rate": 0.05,
        "ip_change_interval": (30, 120),  # 30s-2min
        "ip_change_probability": 0.6,
        "session_duration": (60, 300),
        "user_agent_rotation": 0.3,
        "device_types": ["browser"],
    },
    "attack": {
        "delay_range": (0.1, 1.0),
        "error_rate": 0.10,
        "ip_change_interval": (1, 5),  # 1-5 seconds
        "ip_change_probability": 1.0,  # Always change
        "session_duration": (10, 60),
        "user_agent_rotation": 0.8,
        "device_types": ["browser", "bot"],
    }
}

# ============ IP MANAGER WITH REALISTIC PATTERNS ============
class IPManager:
    def __init__(self):
        self.user_data = {}  # user_id -> {current_ip, history, last_change, sessions}
        self.ip_pool = ALL_IPS.copy()
        random.shuffle(self.ip_pool)
        self.ip_index = 0
        self._lock = threading.Lock()
    
    def _get_ip_category(self, ip: str) -> str:
        """Get the category of an IP"""
        for category, ips in IP_POOL.items():
            if ip in ips:
                return category
        return "unknown"
    
    def _get_random_ip(self, exclude_ip: str = None, preferred_category: str = None) -> str:
        """Get a random IP, optionally excluding one and preferring a category"""
        if preferred_category and preferred_category in IP_POOL:
            candidates = [ip for ip in IP_POOL[preferred_category] if ip != exclude_ip]
            if candidates:
                return random.choice(candidates)
        
        # Fallback to any IP
        candidates = [ip for ip in ALL_IPS if ip != exclude_ip]
        return random.choice(candidates) if candidates else random.choice(ALL_IPS)
    
    def get_ip_for_user(self, user_id: int, user_type: str = "normal") -> tuple[str, bool]:
        """
        Get IP for a user with realistic patterns.
        Returns (ip, is_changed)
        """
        with self._lock:
            behavior = USER_BEHAVIORS.get(user_type, USER_BEHAVIORS["normal"])
            now = time.time()
            
            # Initialize user data
            if user_id not in self.user_data:
                initial_ip = self._get_random_ip()
                self.user_data[user_id] = {
                    "current_ip": initial_ip,
                    "ip_history": [initial_ip],
                    "last_change": now,
                    "next_change": now + random.uniform(*behavior["ip_change_interval"]),
                    "session_start": now,
                    "session_end": now + random.uniform(*behavior["session_duration"]),
                    "current_category": self._get_ip_category(initial_ip),
                    "request_count": 0,
                }
                return initial_ip, False
            
            user = self.user_data[user_id]
            user["request_count"] += 1
            
            # Check if session expired (user comes back later)
            if now > user["session_end"]:
                # New session - could be same user coming back
                if random.random() < 0.3:  # 30% chance they use a different IP
                    new_ip = self._get_random_ip(exclude_ip=user["current_ip"])
                    user["current_ip"] = new_ip
                    user["ip_history"].append(new_ip)
                    user["last_change"] = now
                    user["current_category"] = self._get_ip_category(new_ip)
                    user["request_count"] = 1
                    return new_ip, True
                else:
                    # Same IP, new session
                    user["session_start"] = now
                    user["session_end"] = now + random.uniform(*behavior["session_duration"])
                    user["request_count"] = 1
                    return user["current_ip"], False
            
            # Check if it's time to change IP
            if now > user["next_change"]:
                if random.random() < behavior["ip_change_probability"]:
                    # Realistic IP change - maybe same category, maybe different
                    if random.random() < 0.6:  # 60% chance same category
                        new_ip = self._get_random_ip(
                            exclude_ip=user["current_ip"],
                            preferred_category=user["current_category"]
                        )
                    else:
                        # Different category (user moved to different location)
                        new_ip = self._get_random_ip(exclude_ip=user["current_ip"])
                    
                    user["current_ip"] = new_ip
                    user["ip_history"].append(new_ip)
                    user["last_change"] = now
                    user["current_category"] = self._get_ip_category(new_ip)
                    
                    # Set next change
                    user["next_change"] = now + random.uniform(*behavior["ip_change_interval"])
                    return new_ip, True
            
            # Reset timer if it somehow passed without change
            if now > user["next_change"]:
                user["next_change"] = now + random.uniform(*behavior["ip_change_interval"])
            
            return user["current_ip"], False
    
    def get_user_agent(self, user_id: int, user_type: str) -> str:
        """Get realistic user agent with occasional rotation"""
        behavior = USER_BEHAVIORS.get(user_type, USER_BEHAVIORS["normal"])
        
        if user_id not in self.user_data:
            device_type = random.choice(behavior["device_types"])
            return random.choice(USER_AGENTS[device_type])
        
        user = self.user_data[user_id]
        
        # Check if we should rotate user agent
        if random.random() < behavior["user_agent_rotation"]:
            device_type = random.choice(behavior["device_types"])
            return random.choice(USER_AGENTS[device_type])
        
        # Keep existing user agent if we have one
        if "user_agent" not in user:
            device_type = random.choice(behavior["device_types"])
            user["user_agent"] = random.choice(USER_AGENTS[device_type])
        
        return user["user_agent"]
    
    def get_ip_history(self, user_id: int) -> list:
        """Get IP history for a user"""
        with self._lock:
            if user_id in self.user_data:
                return self.user_data[user_id]["ip_history"]
            return []
    
    def get_stats(self) -> dict:
        """Get IP manager statistics"""
        with self._lock:
            total_changes = 0
            for user in self.user_data.values():
                total_changes += len(user["ip_history"]) - 1
            
            ip_changes_by_user = {
                uid: len(data["ip_history"]) - 1 
                for uid, data in self.user_data.items()
            }
            
            return {
                "unique_users": len(self.user_data),
                "total_ips_used": len(set(ip for data in self.user_data.values() for ip in data["ip_history"])),
                "ip_changes": total_changes,
                "users_with_changes": sum(1 for h in ip_changes_by_user.values() if h > 0),
                "max_changes": max(ip_changes_by_user.values()) if ip_changes_by_user else 0,
                "avg_changes": total_changes / len(self.user_data) if self.user_data else 0,
            }

ip_manager = IPManager()

# ============ HELPER FUNCTIONS ============
def random_headers(user_type: str, user_id: int) -> dict:
    """Generate headers with consistent or rotating IP"""
    ip, ip_changed = ip_manager.get_ip_for_user(user_id, user_type)
    user_agent = ip_manager.get_user_agent(user_id, user_type)
    
    headers = {
        "X-API-KEY": API_KEY,
        "User-Agent": user_agent,
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
    
    # Add referer for realistic browsing
    if random.random() < 0.6:
        referers = [
            "https://www.google.com/search?q=api",
            "https://example.com/page",
            "https://docs.example.com",
            None
        ]
        headers["Referer"] = random.choice(referers)
    
    return headers

# ============ USER BEHAVIORS ============

def normal_user_behavior(user_id: int, stop_event: threading.Event):
    """Normal user with consistent IP and occasional changes"""
    session_endpoints = []
    request_count = 0
    
    print(f"✅ Starting normal user {user_id}")
    
    while not stop_event.is_set():
        try:
            # Rotate endpoints occasionally
            if len(session_endpoints) < 3 or random.random() < 0.3:
                session_endpoints = random.sample(NORMAL_ENDPOINTS, min(3, len(NORMAL_ENDPOINTS)))
            
            endpoint = random.choice(session_endpoints)
            
            # Add realistic search queries
            if endpoint == "/api/search" and random.random() < 0.4:
                search_terms = ["laptop", "phone", "tablet", "book", "monitor", "keyboard", "mouse", "desk"]
                q = random.choice(search_terms)
                endpoint = f"/api/search?q={q}"
            
            headers = random_headers("normal", user_id)
            ip = headers.get("X-Forwarded-For")
            
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            request_count += 1
            
            # Simulate occasional errors
            if random.random() < 0.02:
                # Random 404 or other errors
                headers["Accept"] = "text/html"
                requests.get(f"{BASE_URL}/api/missing", headers=headers, timeout=3)
            
            # Log rate limiting
            if response.status_code == 429:
                print(f"\n⚠️  Rate limited: Normal User {user_id} at {endpoint} (IP: {ip})")
            
            # Human-like delay with some variation
            delay = random.uniform(*USER_BEHAVIORS["normal"]["delay_range"])
            
            # Occasionally browse faster (like clicking through pages)
            if random.random() < 0.2:
                delay = random.uniform(0.5, 1.5)
            
            time.sleep(delay)
            
        except Exception as e:
            print(f"\n❌ Normal user {user_id} error: {e}")
            time.sleep(random.uniform(1.0, 3.0))

def suspicious_user_behavior(user_id: int, stop_event: threading.Event):
    """Suspicious user with consistent IP but faster requests"""
    request_count = 0
    
    print(f"⚠️  Starting suspicious user {user_id}")
    
    while not stop_event.is_set():
        try:
            # More aggressive endpoint selection
            if random.random() < 0.7:
                endpoint = random.choice(NORMAL_ENDPOINTS)
            else:
                endpoint = random.choice(SUSPICIOUS_ENDPOINTS)
            
            # Sometimes hit sensitive endpoints
            if random.random() < 0.3:
                endpoint = "/api/data"
            
            headers = random_headers("suspicious", user_id)
            ip = headers.get("X-Forwarded-For")
            
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            request_count += 1
            
            # Simulate errors
            if random.random() < 0.05:
                requests.get(f"{BASE_URL}/api/sensitive", headers=headers, timeout=3)
            
            if response.status_code == 429:
                print(f"\n⚠️  Suspicious user {user_id} rate limited at {endpoint} (IP: {ip})")
            
            time.sleep(random.uniform(*USER_BEHAVIORS["suspicious"]["delay_range"]))
            
        except Exception as e:
            print(f"\n❌ Suspicious user {user_id} error: {e}")
            time.sleep(random.uniform(0.5, 1.5))

def attack_user_behavior(user_id: int, stop_event: threading.Event):
    """Attack user with rotating IPs and aggressive patterns"""
    attack_count = 0
    max_attacks = random.randint(10, 25)
    
    print(f"🔴 Starting attack user {user_id} ({max_attacks} attacks)")
    
    while not stop_event.is_set() and attack_count < max_attacks:
        try:
            attack_type = random.choice(["brute_force", "scanning", "injection", "dos"])
            
            if attack_type == "brute_force":
                passwords = ["admin123", "password123", "123456", "admin", "root", "qwerty", "letmein"]
                for pwd in random.sample(passwords, min(3, len(passwords))):
                    headers = random_headers("attack", user_id)
                    response = requests.post(
                        f"{BASE_URL}/login",
                        json={"username": "admin", "password": pwd},
                        headers=headers,
                        timeout=3
                    )
                    attack_count += 1
                    if attack_count % 3 == 0:
                        print(f"\n🔴 Attack {attack_count}/{max_attacks}: Brute force attempt")
                    time.sleep(random.uniform(0.2, 0.5))
            
            elif attack_type == "scanning":
                endpoints = random.sample(ATTACK_ENDPOINTS, min(3, len(ATTACK_ENDPOINTS)))
                for endpoint in endpoints:
                    headers = random_headers("attack", user_id)
                    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=3)
                    attack_count += 1
                    if attack_count % 3 == 0:
                        print(f"\n🔴 Attack {attack_count}/{max_attacks}: Scanning {endpoint}")
                    time.sleep(random.uniform(0.1, 0.4))
            
            elif attack_type == "injection":
                payloads = ["' OR '1'='1", "admin'--", "1' AND 1=1--", "' UNION SELECT NULL--", "'; DROP TABLE users--"]
                payload = random.choice(payloads)
                headers = random_headers("attack", user_id)
                response = requests.get(
                    f"{BASE_URL}/api/search?q={payload}",
                    headers=headers,
                    timeout=3
                )
                attack_count += 1
                if attack_count % 3 == 0:
                    print(f"\n🔴 Attack {attack_count}/{max_attacks}: Injection attempt")
                time.sleep(random.uniform(0.3, 0.7))
            
            elif attack_type == "dos":
                # Rapid requests to cause rate limiting
                for _ in range(random.randint(5, 10)):
                    headers = random_headers("attack", user_id)
                    response = requests.get(
                        f"{BASE_URL}/api/profile",
                        headers=headers,
                        timeout=2
                    )
                    attack_count += 1
                    if attack_count % 5 == 0:
                        print(f"\n🔴 Attack {attack_count}/{max_attacks}: DoS attempt")
                    time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 2.0))
            
        except Exception as e:
            print(f"\n❌ Attack user {user_id} error: {e}")
            time.sleep(random.uniform(0.5, 1.0))
    
    # After attacks, behave normally but with different IP
    if attack_count >= max_attacks:
        print(f"\n✅ Attack user {user_id} completed {attack_count} attacks")
        # Continue as normal user with same identity
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
        print(f"🌐 IP Pool Size: {len(ALL_IPS)} unique IPs")
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
                      f"Users: {ip_stats['unique_users']} | "
                      f"IP Changes: {ip_stats['ip_changes']} | "
                      f"Avg Changes: {ip_stats['avg_changes']:.1f} | "
                      f"Max Changes: {ip_stats['max_changes']}", end="", flush=True)
                
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
        print(f"📊 Average IP changes per user: {ip_stats['avg_changes']:.1f}")
        print(f"🔥 Max IP changes: {ip_stats['max_changes']}")
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