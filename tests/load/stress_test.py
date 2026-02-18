import asyncio
import aiohttp
import time
import random
import uuid
import argparse
from typing import List, Dict

# Configuration
BASE_URL = "https://ichigo253-ai-interview-backend.hf.space/api"
CONCURRENT_USERS = 10
TOTAL_REQUESTS = 50

async def user_flow(session: aiohttp.ClientSession, user_id: int):
    email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    full_name = f"Load Test User {user_id}"
    
    # 1. Login (Test DB Load)
    try:
        async with session.post(f"{BASE_URL}/auth/login", json={
            "email": email, # Random email, likely 401
            "password": password
        }) as resp:
            # 200 = Success, 401 = Invalid Creds (Good, means DB checked)
            if resp.status not in [200, 401]:
                text = await resp.text()
                print(f"User {user_id}: Login failed {resp.status} - {text}")
                return False
            
            # If 200, we got a token (unlikely with random creds)
            if resp.status == 200:
                 pass
                 
        return True
        
    except Exception as e:
        print(f"User {user_id}: Exception {e}")
        return False

async def main():
    parser = argparse.ArgumentParser(description="Load Test")
    parser.add_argument("--url", default=BASE_URL, help="Base URL")
    parser.add_argument("--users", type=int, default=CONCURRENT_USERS, help="Concurrent users")
    args = parser.parse_args()
    
    print(f"Starting load test against {args.url} with {args.users} users...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [user_flow(session, i) for i in range(args.users)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
    success_count = sum(results)
    duration = end_time - start_time
    print(f"\n--- Results ---")
    print(f"Total Users: {args.users}")
    print(f"Successful Flows: {success_count}")
    print(f"Failed Flows: {len(results) - success_count}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"RPS: {args.users / duration:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
