print("DEBUG: Script started", flush=True)
import os
import asyncio
print("DEBUG: Importing ProductionAgent", flush=True)
from app.routers.agent import ProductionAgent
print("DEBUG: Importing FastAPI and app", flush=True)
from fastapi import FastAPI
from app.server import app as real_app
print("DEBUG: All imports successful", flush=True)

async def test_agent_robustness():
    print("Initializing test...")
    # Map the environment variable explicitly
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("GROQ_API_KEY not found in environment. Please check .env file.")
        return
    else:
        print(f"GROQ_API_KEY found: {groq_key[:10]}...")

    auth_token = "Bearer dummy_admin_token" 
    print(f"Using Auth Token: {auth_token}")
    
    print("Creating ProductionAgent...")
    agent = ProductionAgent(groq_key=groq_key, fastapi_app=real_app, auth_token=auth_token)

    # Test Case 1: Simple Chain (Find candidate -> Get details)
    print("\n--- Testing Complex Chain: Tushar Goyal ---")
    query = "Show me details of candidate Tushar Goyal"
    print(f"Running agent with query: {query}")
    try:
        result = await agent.run(query)
        print(f"Plan: {result.get('plan')}")
        print(f"API Calls: {result.get('api_calls')}")
        print(f"Reply: {result.get('reply')}")
    except Exception as e:
        print(f"Error during agent.run: {str(e)}")

    # Test Case 2: Scheduling
    print("\n--- Testing Multi-Step Scheduling ---")
    query = "Schedule a Technical round for Tushar Goyal tomorrow at 10 AM"
    print(f"Running agent with query: {query}")
    try:
        result = await agent.run(query)
        print(f"Plan: {result.get('plan')}")
        print(f"API Calls: {result.get('api_calls')}")
        print(f"Reply: {result.get('reply')}")
    except Exception as e:
        print(f"Error during agent.run: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_agent_robustness())
