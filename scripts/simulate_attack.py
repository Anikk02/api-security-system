import asyncio
import random
import httpx
import time

BASE_URL = "http://127.0.0.1:8000"

ATTACK_ENDPOINTS = [
    "/api/test",
    "/api/login",
    "/api/admin",
    "/api/payment",
    "/api/reset-password"
]

BOT_AGENTS = [
    "curl/7.68.0",
    "python-requests/2.31.0",
    "sqlmap",
    "scrapy/2.5.0"
]


def get_headers(attacker_id):
    return {
        "User-Agent": random.choice(BOT_AGENTS),
        "X-API-KEY": f"attacker-{attacker_id}"
    }


#  SCANNER ATTACK
async def scanner_attack(client, attacker_id):
    for _ in range(100):
        endpoint = random.choice(ATTACK_ENDPOINTS)

        await client.get(
            BASE_URL + endpoint,
            headers=get_headers(attacker_id)
        )

        await asyncio.sleep(0.05)


# BURST ATTACK
async def burst_attack(client, attacker_id):
    for _ in range(150):
        await client.get(
            BASE_URL + "/api/test",
            headers=get_headers(attacker_id)
        )

        await asyncio.sleep(0.01)


# BOT LOOP (continuous)
async def bot_attack(client, attacker_id):
    while True:
        endpoint = random.choice(ATTACK_ENDPOINTS)

        try:
            await client.get(
                BASE_URL + endpoint,
                headers=get_headers(attacker_id)
            )
        except:
            pass

        await asyncio.sleep(random.uniform(0.01, 0.1))


async def main():
    async with httpx.AsyncClient(timeout=5) as client:

        tasks = []

        # 5 scanners
        for i in range(5):
            tasks.append(scanner_attack(client, i))

        # 5 burst attackers
        for i in range(5):
            tasks.append(burst_attack(client, i))

        # 10 continuous bots
        for i in range(10):
            tasks.append(bot_attack(client, i))

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    print(f"Attack simulation completed in {time.time() - start:.2f}s")