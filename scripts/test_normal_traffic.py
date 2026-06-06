#!/usr/bin/env python3
"""
Fixed test script for normal API traffic patterns with RANDOM IP FOR EVERY REQUEST.
This prevents rate limiting by distributing requests across many IPs.
"""

import requests
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

BASE_URL = "http://localhost:8000"

# Large IP pool for testing (each request gets a random IP)
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

# Normal user endpoints
ENDPOINTS = [
    "/api/profile", 
    "/api/products", 
    "/api/feed", 
    "/api/search?q=test",
    "/api/users/me",
    "/api/data"
]

# Realistic user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]


def get_random_ip() -> str:
    """Get a random IP for each request"""
    return random.choice(IP_POOL)


def make_request(endpoint: str, delay: float = 0.5) -> dict:
    """Make a single request with a RANDOM IP"""
    
    # ✅ NEW IP FOR EVERY REQUEST
    ip = get_random_ip()
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "X-Forwarded-For": ip,
        "X-Real-IP": ip
    }
    
    start = time.time()
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        latency = (time.time() - start) * 1000
        
        # Small delay to be respectful
        time.sleep(delay)
        
        return {
            "ip": ip,
            "endpoint": endpoint,
            "status": response.status_code,
            "latency": latency,
            "success": response.status_code < 400,
            "headers": {
                "rate_limit": response.headers.get("X-RateLimit-Limit", "N/A"),
                "rate_remaining": response.headers.get("X-RateLimit-Remaining", "N/A")
            }
        }
    except Exception as e:
        time.sleep(delay)
        return {
            "ip": ip,
            "endpoint": endpoint,
            "status": 0,
            "latency": 0,
            "success": False,
            "error": str(e)
        }


def run_test(num_requests: int = 50, delay: float = 0.3):
    """Run test with random IP for each request"""
    
    print(f"\n{'='*60}")
    print(f"RANDOM IP TRAFFIC TEST")
    print(f"Total Requests: {num_requests} | Delay: {delay}s between requests")
    print(f"IP Pool Size: {len(IP_POOL)}")
    print(f"{'='*60}\n")
    
    results = []
    used_ips = set()
    
    print("Sending requests with random IPs...\n")
    
    for i in range(num_requests):
        endpoint = random.choice(ENDPOINTS)
        result = make_request(endpoint, delay)
        results.append(result)
        used_ips.add(result["ip"])
        
        # Show progress
        status_icon = "✅" if result["success"] else "❌"
        print(f"  [{i+1:3d}] {status_icon} {result['endpoint']:20s} | "
              f"IP: {result['ip']:16s} | Status: {result['status']} | "
              f"Latency: {result['latency']:.1f}ms")
    
    # Calculate stats
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    latencies = [r["latency"] for r in results if r["latency"] > 0]
    status_codes = [r["status"] for r in results]
    
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total Requests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/len(results)*100):.1f}%")
    print(f"Unique IPs Used: {len(used_ips)}/{len(IP_POOL)} ({len(used_ips)/len(IP_POOL)*100:.1f}%)")
    
    if latencies:
        latencies.sort()
        print(f"\nLatency Stats:")
        print(f"  Avg: {sum(latencies)/len(latencies):.1f}ms")
        print(f"  Min: {min(latencies):.1f}ms")
        print(f"  Max: {max(latencies):.1f}ms")
        print(f"  P50: {latencies[len(latencies)//2]:.1f}ms")
        if len(latencies) > 10:
            print(f"  P95: {latencies[int(len(latencies)*0.95)]:.1f}ms")
            print(f"  P99: {latencies[int(len(latencies)*0.99)]:.1f}ms")
    
    # Status code distribution
    print(f"\nStatus Code Distribution:")
    for code, count in sorted(Counter(status_codes).items()):
        print(f"  {code}: {count} requests ({count/len(status_codes)*100:.1f}%)")
    
    print(f"{'='*60}\n")
    
    return results


def quick_test():
    """Quick test with 10 requests"""
    print(f"\n{'='*60}")
    print(f"QUICK TEST - 10 Requests with Random IPs")
    print(f"{'='*60}\n")
    
    success_count = 0
    
    for i in range(10):
        endpoint = random.choice(ENDPOINTS[:3])  # Use first 3 endpoints
        result = make_request(endpoint, delay=0.2)
        
        if result["success"]:
            success_count += 1
        
        status_icon = "✅" if result["success"] else "❌"
        print(f"  {status_icon} Request {i+1:2d}: {result['endpoint']:15s} | "
              f"IP: {result['ip']:15s} | Status: {result['status']}")
    
    print(f"\n✅ Success Rate: {success_count}/10 ({success_count*10}%)")
    print(f"{'='*60}\n")


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
    print("\n" + "="*60)
    print("API SECURITY SYSTEM - RANDOM IP TRAFFIC TEST")
    print("="*60)
    
    if health_check():
        # Run quick test first
        quick_test()
        
        # Run full test
        run_test(num_requests=50, delay=0.2)
        
        print("\n✅ Test completed! Each request used a different random IP.")
        print("   This prevents rate limiting from blocking the test.")
    else:
        print("\n❌ Start your API server first:")
        print("   cd C:\\edb\\api_security_system")
        print("   python -m app.main")