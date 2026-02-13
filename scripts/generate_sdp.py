import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription

async def generate_offer():
    pc = RTCPeerConnection()
    
    # Create a dummy data channel or track to ensure SDP has media sections
    pc.addTransceiver('video', direction='sendrecv')
    
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    
    payload = {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
        "interview_id": 1  # Default to ID 1 for testing
    }
    
    print("\n" + "="*50)
    print("✅ COPY THIS JSON INTO SWAGGER (POST /api/analyze/video/offer)")
    print("="*50)
    print(json.dumps(payload, indent=2))
    print("="*50 + "\n")
    
    await pc.close()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generate_offer())
