from aiortc import MediaStreamTrack
import av
import logging
import json
from typing import Optional
from .camera import CameraService

logger = logging.getLogger(__name__)

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an input track.
    It applies Face & Gaze detection using the CameraService.
    Can optionally send real-time AI results over a WebRTC DataChannel.
    """
    kind = "video"

    def __init__(self, track, interview_id: Optional[int] = None, channel=None):
        super().__init__()
        self.track = track
        self.camera_service = CameraService()  # Singleton
        self.interview_id = interview_id
        self.channel = channel
        self.frame_count = 0
        logger.info(f"WebRTC Track Initialized for Session: {interview_id} (DataChannel: {bool(channel)})")

    async def recv(self):
        try:
            frame = await self.track.recv()
            self.frame_count += 1
            
            # Convert WebRTC frame to numpy (BGR)
            img = frame.to_ndarray(format="bgr24")
            
            # Process: detection + annotation + AI analysis
            annotated_img, results = self.camera_service.process_frame_ndarray(img, self.interview_id)
            
            # PUSH TO DATA CHANNEL: This replaces the need for REST API polling!
            if self.channel and self.channel.readyState == "open":
                try:
                    self.channel.send(json.dumps({
                        "type": "proctoring_update",
                        "interview_id": self.interview_id,
                        "data": results,
                        "frame_id": self.frame_count
                    }))
                except Exception as e:
                    logger.debug(f"DataChannel Send Error: {e}")

            # Convert back to WebRTC frame
            new_frame = av.VideoFrame.from_ndarray(annotated_img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
            
        except Exception as e:
            logger.error(f"WebRTC: Frame Error Session {self.interview_id}: {e}")
            if 'frame' in locals():
                return frame
            raise
