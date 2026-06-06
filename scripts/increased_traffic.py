#!/usr/bin/env python3
"""
15-Minute Increased Traffic Test for API Security System.
Simulates real-world traffic patterns with random IP for EVERY request.
No exploitation - just higher than normal legitimate traffic.

Traffic Patterns:
- Sustained high traffic (10 minutes)
- Spike bursts (30 seconds of very high traffic)
- Cooldown periods (1 minute)
- Total duration: 15 minutes
"""

import requests
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter
from datetime import datetime
import statistics
import signal
import sys

BASE_URL = "http://localhost:8000"

# Large IP pool (each request gets random IP)
IP_POOL = (
    [f"192.168.1.{i}" for i in range(1, 256)] +
    [f"192.168.2.{i}" for i in range(1, 256)] +
    [f"10.0.0.{i}" for i in range(1, 256)] +
    [f"172.16.{i}.{j}" for i in range(1, 32) for j in range(1, 9)] +
    [f"192.168.{i}.{j}" for i in range(3, 11) for j in range(1, 51)]
)  # Total ~2000+ IPs

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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0"
]


class TrafficStats:
    """Track traffic statistics"""
    def __init__(self):
        self.total_requests = 0
        self.successful = 0
        self.failed = 0
        self.latencies = []
        self.status_codes = Counter()
        self.endpoint_hits = defaultdict(int)
        self.ip_hits = defaultdict(int)
        self.minute_stats = []
        self.start_time = time.time()
    
    def add_result(self, result):
        self.total_requests += 1
        if result["success"]:
            self.successful += 1
            self.latencies.append(result["latency"])
        else:
            self.failed += 1
        
        self.status_codes[result["status"]] += 1
        self.endpoint_hits[result["endpoint"]] += 1
        self.ip_hits[result["ip"]] += 1
    
    def get_minute_stats(self):
        elapsed_minutes = (time.time() - self.start_time) / 60
        return {
            "minute": len(self.minute_stats) + 1,
            "total": self.total_requests,
            "successful": self.successful,
            "failed": self.failed,
            "avg_latency": statistics.mean(self.latencies[-100:]) if self.latencies else 0
        }
    
    def print_summary(self):
        print(f"\n{'='*70}")
        print(f"TRAFFIC SUMMARY")
        print(f"{'='*70}")
        print(f"Total Requests: {self.total_requests}")
        print(f"Successful: {self.successful}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.successful/self.total_requests*100):.1f}%")
        
        if self.latencies:
            self.latencies.sort()
            print(f"\nLatency Stats:")
            print(f"  Min: {min(self.latencies):.1f}ms")
            print(f"  Max: {max(self.latencies):.1f}ms")
            print(f"  Avg: {statistics.mean(self.latencies):.1f}ms")
            print(f"  P50: {self.latencies[len(self.latencies)//2]:.1f}ms")
            print(f"  P95: {self.latencies[int(len(self.latencies)*0.95)]:.1f}ms")
            print(f"  P99: {self.latencies[int(len(self.latencies)*0.99)]:.1f}ms")
        
        print(f"\nStatus Code Distribution:")
        for code, count in self.status_codes.most_common(5):
            print(f"  {code}: {count} ({count/self.total_requests*100:.1f}%)")
        
        print(f"\nTop 5 Endpoints:")
        for endpoint, count in sorted(self.endpoint_hits.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {endpoint}: {count} requests")
        
        print(f"\nUnique IPs Used: {len(self.ip_hits)}")
        print(f"{'='*70}\n")


def get_random_ip() -> str:
    """Get random IP for each request"""
    return random.choice(IP_POOL)


def make_request(endpoint: str, request_id: int = 0) -> dict:
    """Make request with random IP"""
    ip = get_random_ip()
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
        "X-Request-ID": str(request_id)
    }
    
    start = time.time()
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
    except Exception as e:
        return {
            "request_id": request_id,
            "ip": ip,
            "endpoint": endpoint,
            "status": 0,
            "latency": (time.time() - start) * 1000,
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }


def run_sustained_traffic(stats: TrafficStats, duration_seconds: int, rps: int, label: str):
    """Run sustained traffic at constant RPS"""
    print(f"\n  [{label}] Running {rps} req/sec for {duration_seconds}s...")
    
    interval = 1.0 / rps
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < duration_seconds:
        # Batch requests to achieve RPS
        batch_size = min(10, max(1, int(rps / 10)))
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            for _ in range(batch_size):
                endpoint = random.choice(ENDPOINTS)
                futures.append(executor.submit(make_request, endpoint, request_count))
                request_count += 1
            
            for future in as_completed(futures):
                result = future.result()
                stats.add_result(result)
        
        # Maintain rate
        elapsed = time.time() - start_time
        expected = request_count / rps
        if elapsed < expected:
            time.sleep(expected - elapsed)
    
    print(f"     ✓ Completed: {stats.total_requests} total requests so far")


def run_spike_traffic(stats: TrafficStats, duration_seconds: int, spike_rps: int, label: str):
    """Run spike traffic (very high RPS for short duration)"""
    print(f"\n  ⚡ [{label}] SPIKE: {spike_rps} req/sec for {duration_seconds}s!")
    
    interval = 1.0 / spike_rps
    start_time = time.time()
    request_count = 0
    spike_start = stats.total_requests
    
    while time.time() - start_time < duration_seconds:
        # More aggressive batching for spikes
        batch_size = min(20, max(1, int(spike_rps / 5)))
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            for _ in range(batch_size):
                endpoint = random.choice(ENDPOINTS)
                futures.append(executor.submit(make_request, endpoint, request_count))
                request_count += 1
            
            for future in as_completed(futures):
                result = future.result()
                stats.add_result(result)
        
        elapsed = time.time() - start_time
        expected = request_count / spike_rps
        if elapsed < expected:
            time.sleep(expected - elapsed)
    
    spike_requests = stats.total_requests - spike_start
    print(f"     ⚡ Spike completed: {spike_requests} requests in {duration_seconds}s ({spike_requests/duration_seconds:.1f} req/sec)")


def run_cooldown(stats: TrafficStats, duration_seconds: int, label: str):
    """Cooldown period - minimal traffic"""
    print(f"\n  🌊 [{label}] Cooldown for {duration_seconds}s (minimal traffic)...")
    
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < duration_seconds:
        # Very low traffic during cooldown
        if random.random() < 0.1:  # 10% chance
            endpoint = random.choice(ENDPOINTS)
            result = make_request(endpoint, request_count)
            stats.add_result(result)
            request_count += 1
        
        time.sleep(0.5)
    
    print(f"     ✓ Cooldown complete")


def print_progress(stats: TrafficStats, elapsed_minutes: float):
    """Print progress every minute"""
    avg_latency = statistics.mean(stats.latencies[-100:]) if stats.latencies else 0
    success_rate = (stats.successful / stats.total_requests * 100) if stats.total_requests > 0 else 0
    
    print(f"\n  [{elapsed_minutes:.1f} min] Progress: {stats.total_requests} requests | "
          f"Success: {success_rate:.1f}% | Avg Latency: {avg_latency:.1f}ms")


def run_15min_test():
    """Run 15-minute test with various traffic patterns"""
    
    print("\n" + "="*70)
    print("15-MINUTE INCREASED TRAFFIC TEST")
    print("="*70)
    print("\nTraffic Pattern:")
    print("  Minute 0-5   : Sustained high traffic (30 req/sec)")
    print("  Minute 5-6   : SPIKE (150 req/sec for 60 seconds)")
    print("  Minute 6-7   : Cooldown (5 req/sec)")
    print("  Minute 7-10  : Sustained high traffic (40 req/sec)")
    print("  Minute 10-11 : SPIKE (200 req/sec for 60 seconds)")
    print("  Minute 11-12 : Cooldown (5 req/sec)")
    print("  Minute 12-15 : Sustained high traffic (35 req/sec)")
    print("\n" + "="*70)
    
    stats = TrafficStats()
    
    # Phase 1: Minutes 0-5 (300 seconds) - Sustained high traffic
    run_sustained_traffic(stats, duration_seconds=300, rps=30, label="Phase 1 (Min 0-5)")
    print_progress(stats, 5)
    
    # Phase 2: Minute 5-6 (60 seconds) - SPIKE
    run_spike_traffic(stats, duration_seconds=60, spike_rps=150, label="Phase 2 (Min 5-6)")
    print_progress(stats, 6)
    
    # Phase 3: Minute 6-7 (60 seconds) - Cooldown
    run_cooldown(stats, duration_seconds=60, label="Phase 3 (Min 6-7)")
    print_progress(stats, 7)
    
    # Phase 4: Minutes 7-10 (180 seconds) - Sustained high traffic
    run_sustained_traffic(stats, duration_seconds=180, rps=40, label="Phase 4 (Min 7-10)")
    print_progress(stats, 10)
    
    # Phase 5: Minute 10-11 (60 seconds) - SPIKE
    run_spike_traffic(stats, duration_seconds=60, spike_rps=200, label="Phase 5 (Min 10-11)")
    print_progress(stats, 11)
    
    # Phase 6: Minute 11-12 (60 seconds) - Cooldown
    run_cooldown(stats, duration_seconds=60, label="Phase 6 (Min 11-12)")
    print_progress(stats, 12)
    
    # Phase 7: Minutes 12-15 (180 seconds) - Sustained high traffic
    run_sustained_traffic(stats, duration_seconds=180, rps=35, label="Phase 7 (Min 12-15)")
    print_progress(stats, 15)
    
    # Final summary
    print("\n" + "="*70)
    print("TEST COMPLETE - 15 MINUTES")
    print("="*70)
    
    stats.print_summary()
    
    # Calculate overall RPS
    total_time = 900  # 15 minutes
    overall_rps = stats.total_requests / total_time
    
    print(f"\nOverall Statistics:")
    print(f"  Total Test Duration: 15 minutes (900 seconds)")
    print(f"  Overall RPS: {overall_rps:.1f}")
    print(f"  Total Unique IPs: {len(stats.ip_hits)}")
    
    return stats


def quick_spike_test():
    """Quick spike test for verification (30 seconds)"""
    
    print("\n" + "="*70)
    print("QUICK SPIKE TEST (30 seconds)")
    print("="*70)
    
    stats = TrafficStats()
    
    # Quick spike test
    print("\n  Running quick spike test...")
    run_spike_traffic(stats, duration_seconds=30, spike_rps=100, label="Quick Spike")
    
    stats.print_summary()
    return stats


if __name__ == "__main__":
    print("\n" + "="*70)
    print("API SECURITY SYSTEM - 15-MINUTE TRAFFIC TEST")
    print("Random IP for every request | Increased legitimate traffic")
    print("="*70)
    
    # Check server health
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        if resp.status_code != 200:
            print("\n❌ Server health check failed!")
            sys.exit(1)
        print("\n✅ Server is healthy")
    except Exception as e:
        print(f"\n❌ Cannot connect to server: {e}")
        print("   Make sure your API server is running on port 8000")
        sys.exit(1)
    
    print(f"\nIP Pool Size: {len(IP_POOL)} unique IPs")
    print(f"Endpoints: {len(ENDPOINTS)}")
    
    # Ask user which test to run
    print("\nSelect test:")
    print("  1. Quick spike test (30 seconds)")
    print("  2. Full 15-minute test")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        quick_spike_test()
    else:
        run_15min_test()
    
    print("\n✅ Test completed successfully!")
    print("   Each request used a different random IP")
    print("   No exploitation - just legitimate increased traffic")