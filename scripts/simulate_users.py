import asyncio
import random
import httpx
import time

BASE_URL = "http://localhost:8000"

# USER AGENTS
USER_AGENTS = [
    # browsers
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X) Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Firefox/119.0",

    # bots/tools
    "curl/7.68.0",
    "python-requests/2.28",
    "Googlebot/2.1",
    "Scrapy/2.8",
]

# ENDPOINT POOL
NORMAL_ENDPOINTS = [
    "/api/data",
    "/api/test",
    "/api/profile",
    "/health"
]

SENSITIVE_ENDPOINTS = [
    "/login",
    "/admin",
    "/config",
    "/reset-password"
]

# UTIL
def random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def random_headers(label):
    return {
        "X-Forwarded-For": random_ip(),
        "User-Agent": random.choice(USER_AGENTS),
        "X-Simulated-Label": label 
    }

# USER TYPES

#  NORMAL USER
async def normal_user():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
        for _ in range(random.randint(50, 150)):
            try:
                await client.get(
                    random.choice(NORMAL_ENDPOINTS),
                    headers=random_headers("normal")
                )
            except:
                pass

            await asyncio.sleep(random.uniform(0.5, 2.0))


#  SUSPICIOUS USER
async def suspicious_user():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
        for _ in range(random.randint(80, 200)):
            try:
                await client.get(
                    random.choice(["/api/data", "/api/data", "/api/test"]),
                    headers=random_headers("suspicious")
                )
            except:
                pass

            await asyncio.sleep(random.uniform(0.1, 0.4))


#  BRUTE FORCE ATTACK
async def brute_force_user():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
        for _ in range(random.randint(150, 300)):
            try:
                await client.post(
                    "/login",
                    json={"username": "admin", "password": "wrong"},
                    headers=random_headers("attack")
                )
            except:
                pass

            await asyncio.sleep(0.03)


#  SCANNER
async def scanner_user():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
        for _ in range(random.randint(100, 250)):
            try:
                await client.get(
                    random.choice(SENSITIVE_ENDPOINTS),
                    headers=random_headers("attack")
                )
            except:
                pass

            await asyncio.sleep(0.05)


#  SCRAPER
async def scraper_user():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
        for _ in range(random.randint(150, 300)):
            try:
                await client.get(
                    "/api/data",
                    headers=random_headers("attack")
                )
            except:
                pass

            await asyncio.sleep(0.02)

# RUNNER
async def main():
    tasks = []

    # normal users
    for _ in range(20):
        tasks.append(normal_user())

    # suspicious
    for _ in range(10):
        tasks.append(suspicious_user())

    # attackers
    for _ in range(5):
        tasks.append(brute_force_user())

    for _ in range(5):
        tasks.append(scanner_user())

    for _ in range(5):
        tasks.append(scraper_user())

    start = time.time()

    await asyncio.gather(*tasks)

    print(f"\nSimulation completed in {time.time() - start:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())