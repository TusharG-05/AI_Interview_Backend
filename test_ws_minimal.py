#!/usr/bin/env python3
"""Test minimal WS endpoint (no auth required)"""
import asyncio
import websockets
import json

async def test():
    uri = "ws://127.0.0.1:8000/api/test-ws"
    print(f"🔗 Connecting to: {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Receive the test message
            msg = await websocket.recv()
            print(f"📨 Received: {msg}")
            
            # Try to keep connection alive for a few seconds
            await asyncio.sleep(3)
            print("✅ Connection maintained for 3 seconds")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
