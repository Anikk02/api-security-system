#!/usr/bin/env python3
"""
Extreme High Rate Test - 10 minutes at 500+ req/sec.
Does NOT affect persistent config - only Redis runtime state (auto-expires).
Each request uses random IP to distribute load.
"""

import requests
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter
from datetime import datetime
import statistics
import sys
import signal

BASE_URL = "http://localhost:8000"

# Massive IP pool (each request gets random IP to distribute load)
IP_POOL = (
    [f"192.168.1.{i}" for i in range(1, 256)] +
    [f"192.168.2.{i}" for i in range(1, 256)] +
    [f"10.0.0.{i}" for i in range(1, 256)] +
    [f"172.16.{i}.{j}" for i in range(1, 32) for j in range(1, 9)] +
    [f"192.168.{i}.{j}" for i in range(3, 11) for j in range(1, 51)] +
    [f"10.{i}.{j}.{k}" for i in range(1, 3) for j in range(1, 50) for k in range(1, 50)]
)  # Total ~5000+ IPs

# Endpoints (normal API endpoints)
ENDPOINTS = [
    "/api/profile",
    "/api/products",
    "/api/feed",
    "/api/search?q=test",
    "/api/users/me",
    "/api/data"
]

# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Firefox/121.0"
]

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    global running
    print("\n\n⚠️ Received interrupt signal. Shutting down gracefully...")
    running = False

signal.signal(signal.SIGINT, signal_handler)


class ExtremeTrafficStats:
    """Track statistics during extreme load"""
    def __init__(self):
        self.total_requests = 0
        self.successful = 0
        self.failed = 0
        self.latencies = []
        self.status_codes = Counter()
        self.errors = []
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.request_times = []
    
    def add_result(self, result):
        with self.lock:
            self.total_requests += 1
            self.request_times.append(result["timestamp"])
            if result["success"]:
                self.successful += 1
                self.latencies.append(result["latency"])
            else:
                self.failed += 1
                if result.get("error"):
                    self.errors.append(result["error"])
            
            self.status_codes[result["status"]] += 1
    
    def get_rps(self, last_n_seconds=10):
        """Calculate current RPS over last N seconds"""
        with self.lock:
            if not self.request_times:
                return 0
            now = time.time()
            cutoff = now - last_n_seconds
            recent = [t for t in self.request_times if t > cutoff]
            return len(recent) / last_n_seconds
    
    def print_progress(self):
        """Print progress every 30 seconds"""
        elapsed = time.time() - self.start_time
        minutes = elapsed / 60
        rps = self.get_rps(10)
        success_rate = (self.successful / self.total_requests * 100) if self.total_requests > 0 else 0
        
        print(f"[{minutes:5.1f} min] Requests: {self.total_requests:,} | "
              f"RPS: {rps:.0f} | Success: {success_rate:.1f}% | "
              f"Latency: {statistics.mean(self.latencies[-100:]):.1f}ms" if self.latencies else "N/A")


def get_random_ip() -> str:
    """Get random IP for each request"""
    return random.choice(IP_POOL)


def make_request(request_id: int) -> dict:
    """Make single request with random IP"""
    ip = get_random_ip()
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
        "X-Request-ID": str(request_id),
        "Connection": "close"  # Don't keep connections open
    }
    
    endpoint = random.choice(ENDPOINTS)
    start = time.time()
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        latency = (time.time() - start) * 1000
        
        return {
            "request_id": request_id,
            "ip": ip,
            "endpoint": endpoint,
            "status": response.status_code,
            "latency": latency,
            "success": response.status_code < 400,
            "timestamp": time.time()
        }
    except requests.exceptions.Timeout:
        return {
            "request_id": request_id,
            "ip": ip,
            "endpoint": endpoint,
            "status": 0,
            "latency": (time.time() - start) * 1000,
            "success": False,
            "error": "Timeout",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "request_id": request_id,
            "ip": ip,
            "endpoint": endpoint,
            "status": 0,
            "latency": (time.time() - start) * 1000,
            "success": False,
            "error": str(e)[:100],
            "timestamp": time.time()
        }


class ExtremeTrafficGenerator:
    """Generate extreme high rate traffic"""
    
    def __init__(self, target_rps: int = 500, max_workers: int = 100):
        self.target_rps = target_rps
        self.max_workers = max_workers
        self.stats = ExtremeTrafficStats()
        self.request_id = 0
    
    def worker(self, num_requests: int):
        """Worker thread to send requests"""
        for _ in range(num_requests):
            if not running:
                break
            result = make_request(self.request_id)
            self.stats.add_result(result)
            self.request_id += 1
    
    def run_burst(self, duration_seconds: int, burst_rps: int):
        """Run a burst at specific RPS"""
        print(f"\n  🔥 BURST: {burst_rps} req/sec for {duration_seconds}s")
        
        interval = 1.0 / burst_rps
        start_time = time.time()
        sent = 0
        
        while time.time() - start_time < duration_seconds and running:
            # Batch requests to achieve RPS
            batch_size = min(self.max_workers, max(1, int(burst_rps / 10)))
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = [executor.submit(make_request, self.request_id + i) for i in range(batch_size)]
                for future in as_completed(futures):
                    result = future.result()
                    self.stats.add_result(result)
                    self.request_id += 1
                    sent += 1
            
            # Maintain rate
            elapsed = time.time() - start_time
            expected = sent / burst_rps
            if elapsed < expected:
                time.sleep(expected - elapsed)
    
    def run_sustained(self, duration_seconds: int, target_rps: int):
        """Run sustained high rate traffic"""
        print(f"\n  📈 SUSTAINED: {target_rps} req/sec for {duration_seconds}s")
        
        interval = 1.0 / target_rps
        start_time = time.time()
        sent = 0
        
        while time.time() - start_time < duration_seconds and running:
            # Determine batch size (adjust based on target RPS)
            batch_size = min(50, max(1, int(target_rps / 20)))
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = [executor.submit(make_request, self.request_id + i) for i in range(batch_size)]
                for future in as_completed(futures):
                    result = future.result()
                    self.stats.add_result(result)
                    self.request_id += 1
                    sent += 1
            
            # Maintain rate
            elapsed = time.time() - start_time
            expected = sent / target_rps
            if elapsed < expected:
                time.sleep(max(0, expected - elapsed))
            
            # Print progress every 10 seconds
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                self.stats.print_progress()


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


def run_extreme_test():
    """Run extreme high rate test for 10 minutes"""
    
    print("\n" + "="*70)
    print("🔥 EXTREME HIGH RATE TEST - 10 MINUTES 🔥")
    print("="*70)
    print("\n⚠️  WARNING: This test will generate VERY HIGH traffic")
    print("   - Target: 500-1000 requests per second")
    print("   - Duration: 10 minutes")
    print("   - Total requests: 300,000 - 600,000")
    print("\n✅ This will NOT affect persistent config")
    print("   - Only Redis runtime state (auto-expires)")
    print("   - Database records are permanent (audit)")
    print("\nPress Ctrl+C to stop early\n")
    
    generator = ExtremeTrafficGenerator(target_rps=500, max_workers=100)
    stats = generator.stats
    
    # Phase 1: Ramp up (1 minute)
    print("\n" + "="*70)
    print("PHASE 1: Ramping up to 300 req/sec")
    print("="*70)
    generator.run_sustained(60, 300)
    
    if not running:
        return stats
    
    # Phase 2: High sustained (5 minutes)
    print("\n" + "="*70)
    print("PHASE 2: High sustained traffic (500 req/sec)")
    print("="*70)
    generator.run_sustained(300, 500)
    
    if not running:
        return stats
    
    # Phase 3: Extreme peak (2 minutes)
    print("\n" + "="*70)
    print("PHASE 3: Extreme peak (800-1000 req/sec bursts)")
    print("="*70)
    
    for i in range(4):  # 4 bursts of 30 seconds each
        if not running:
            break
        burst_rps = random.choice([800, 900, 1000])
        generator.run_burst(30, burst_rps)
        if running and i < 3:
            print("  ⏸️  Brief cooldown...")
            time.sleep(10)
    
    if not running:
        return stats
    
    # Phase 4: Cool down (2 minutes)
    print("\n" + "="*70)
    print("PHASE 4: Cooling down (200 req/sec)")
    print("="*70)
    generator.run_sustained(120, 200)
    
    return stats


def print_final_summary(stats: ExtremeTrafficStats):
    """Print final test summary"""
    
    elapsed = time.time() - stats.start_time
    minutes = elapsed / 60
    overall_rps = stats.total_requests / elapsed
    
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    print(f"\nTest Duration: {minutes:.1f} minutes ({elapsed:.0f} seconds)")
    print(f"Total Requests: {stats.total_requests:,}")
    print(f"Successful: {stats.successful:,}")
    print(f"Failed: {stats.failed:,}")
    print(f"Success Rate: {(stats.successful/stats.total_requests*100):.1f}%")
    print(f"Overall RPS: {overall_rps:.0f}")
    
    if stats.latencies:
        stats.latencies.sort()
        print(f"\nLatency Stats (successful requests):")
        print(f"  Min: {min(stats.latencies):.1f}ms")
        print(f"  Max: {max(stats.latencies):.1f}ms")
        print(f"  Avg: {statistics.mean(stats.latencies):.1f}ms")
        print(f"  P50: {stats.latencies[len(stats.latencies)//2]:.1f}ms")
        print(f"  P95: {stats.latencies[int(len(stats.latencies)*0.95)]:.1f}ms")
        print(f"  P99: {stats.latencies[int(len(stats.latencies)*0.99)]:.1f}ms")
    
    print(f"\nStatus Code Distribution:")
    for code, count in stats.status_codes.most_common(5):
        print(f"  {code}: {count:,} ({count/stats.total_requests*100:.1f}%)")
    
    print(f"\n⚠️  Note: All Redis state will auto-expire")
    print("   Database logs are permanent (audit)")
    print("="*70)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 API SECURITY SYSTEM - EXTREME HIGH RATE TEST")
    print("="*70)
    
    if not health_check():
        print("\n❌ Start your API server first:")
        print("   cd C:\\edb\\api_security_system")
        print("   python -m app.main")
        sys.exit(1)
    
    print(f"\nIP Pool Size: {len(IP_POOL):,} unique IPs")
    print(f"Endpoints: {len(ENDPOINTS)}")
    
    # Ask for confirmation
    print("\n⚠️  This will generate 300,000+ requests in 10 minutes!")
    confirm = input("\nContinue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Aborted.")
        sys.exit(0)
    
    # Run the test
    stats = run_extreme_test()
    
    # Print results
    print_final_summary(stats)
    
    print("\n✅ Test completed!")
    print("   - All Redis state will expire automatically")
    print("   - Database audit logs preserved")
    print("   - System returned to normal state")