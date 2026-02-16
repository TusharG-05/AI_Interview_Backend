import asyncio
import cv2
import logging
import requests
import av
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCSessionDescription

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stream_camera")

BASE_URL = "http://localhost:8000/api"
INTERVIEW_ID = 1

class CameraStreamTrack(VideoStreamTrack):
    """
    A video track that yields frames from the local webcam using OpenCV.
    """
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        self.pts = 0
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam.")
        logger.info("Webcam opened successfully.")

    async def recv(self):
        # Read frame from OpenCV
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from webcam.")

        # Convert to aiortc VideoFrame
        # OpenCV is in BGR, we keep it BGR because our server expects BGR (or handles it)
        # But aiortc internally prefers format management. 
        # Making it standard: output BGR, server will read.
        video_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
        
        from fractions import Fraction
        
        # Monotonic timestamps
        video_frame.pts = self.pts
        video_frame.time_base = Fraction(1, 30) # 30 FPS
        self.pts += 1
        
        # Artificial delay to match 30 FPS roughly
        await asyncio.sleep(1/30)
        return video_frame

    def stop(self):
        self.cap.release()

async def run_client():
    # 1. Create Peer Connection
    pc = RTCPeerConnection()
    
    # 2. Add Local Camera Track
    try:
        track = CameraStreamTrack()
        pc.addTrack(track)
    except Exception as e:
        logger.error(f"Failed to access camera: {e}")
        return

    # 3. Create Offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    
    # 4. Send to Server
    # 4. Send to Server
    payload = {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
        "interview_id": INTERVIEW_ID
    }
    
    logger.info(f"Sending Offer for Session {INTERVIEW_ID}...")
    logger.info(f"Sending Offer for Session {INTERVIEW_ID}...")
    try:
        response = requests.post(f"{BASE_URL}/analyze/video/offer", json=payload)
        response.raise_for_status()
        data = response.json()
        
        # 5. Handle Answer
        answer_sdp = data["data"]["sdp"]
        answer_type = data["data"]["type"]
        
        answer = RTCSessionDescription(sdp=answer_sdp, type=answer_type)
        await pc.setRemoteDescription(answer)
        logger.info("✅ WebRTC Connection Established! Streaming video...")
        print(f"\n🎥 View your video at: {BASE_URL}/analyze/video/video_feed?interview_id={INTERVIEW_ID}\n")
        
    except Exception as e:
        logger.error(f"Signaling failed: {e}")
        track.stop()
        await pc.close()
        return

    # 6. Keep Alive
    try:
        # Keep the script running to maintain the stream
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Closing connection...")
        track.stop()
        await pc.close()

if __name__ == "__main__":
    asyncio.run(run_client())
