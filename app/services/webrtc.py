from aiortc import MediaStreamTrack
import av
import logging
from typing import Optional
from .camera import CameraService

logger = logging.getLogger(__name__)

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an input track.
    It applies Face & Gaze detection using the CameraService.
    """
    kind = "video"

    def __init__(self, track, interview_id: Optional[int] = None):
        super().__init__()
        self.track = track
        self.camera_service = CameraService()  # Singleton — same instance everywhere
        self.interview_id = interview_id
        self.frame_count = 0
        logger.info(f"WebRTC Track Initialized for Session: {interview_id}")

    async def recv(self):
        try:
            frame = await self.track.recv()
            self.frame_count += 1
            
            # Log every 90 frames (~3 seconds at 30fps)
            if self.frame_count % 90 == 0:
                logger.info(f"WebRTC: Processed {self.frame_count} frames for Session {self.interview_id}")

            # Convert WebRTC frame to numpy (BGR)
            img = frame.to_ndarray(format="bgr24")
            
            # Process: detection + annotation + store in session_frames
            annotated_img, _ = self.camera_service.process_frame_ndarray(img, self.interview_id)
            
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
