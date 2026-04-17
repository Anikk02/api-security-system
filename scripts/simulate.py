import asyncio
import random
import httpx
import time

BASE_URL = "http://localhost:8000"

# ----------- CONFIG ----------- #
USERS = [
    {"ip": "1.1.1.1", "type": "normal"},
    {"ip": "2.2.2.2", "type": "normal"},
    {"ip": "3.3.3.3", "type": "bot"},
    {"ip": "4.4.4.4", "type": "attacker"},
    {"ip": "5.5.5.5", "type": "attacker"},
]

ENDPOINTS = [
    "/api/home",
    "/api/profile",
    "/api/orders",
    "/api/products",
]

ATTACK_ENDPOINTS = [
    "/admin",
    "/.env",
    "/config",
    "/login",
    "/api/secret",
]

# ----------- BEHAVIOR ----------- #

async def normal_user(client, ip):
    """Simulates normal browsing"""
    for _ in range(40):
        endpoint = random.choice(ENDPOINTS)

        await client.get(
            BASE_URL + endpoint,
            headers={"X-Forwarded-For": ip}
        )

        await asyncio.sleep(random.uniform(0.5, 2.0))  # human-like delay


async def bot_user(client, ip):
    """Simulates bot hitting same endpoint rapidly"""
    for _ in range(60):
        await client.get(
            BASE_URL + "/login",
            headers={
                "X-Forwarded-For": ip,
                "User-Agent": "python-requests/2.0"
            }
        )

        await asyncio.sleep(0.05)  # very fast


async def attacker_user(client, ip):
    """Simulates scanning attacker"""
    for _ in range(30):
        endpoint = random.choice(ATTACK_ENDPOINTS)

        await client.get(
            BASE_URL + endpoint,
            headers={"X-Forwarded-For": ip}
        )

        await asyncio.sleep(random.uniform(0.1, 0.3))


# ----------- MAIN RUNNER ----------- #

async def simulate():
    async with httpx.AsyncClient(timeout=10) as client:

        tasks = []

        for user in USERS:
            ip = user["ip"]
            utype = user["type"]

            if utype == "normal":
                tasks.append(normal_user(client, ip))

            elif utype == "bot":
                tasks.append(bot_user(client, ip))

            elif utype == "attacker":
                tasks.append(attacker_user(client, ip))

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    start = time.time()
    asyncio.run(simulate())
    print(f"Simulation completed in {time.time() - start:.2f}s")