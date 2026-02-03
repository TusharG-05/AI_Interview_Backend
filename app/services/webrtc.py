from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
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

    def __init__(self, track, session_id: Optional[int] = None):
        super().__init__()  # don't forget this!
        self.track = track
        self.camera_service = CameraService()
        self.session_id = session_id
        logger.info(f"WebRTC Track Initialized for Session: {session_id}")

    async def recv(self):
        try:
            frame = await self.track.recv()
            
            # Convert WebRTC frame to numpy (BGR)
            # aiortc uses pyav. 
            img = frame.to_ndarray(format="bgr24")
            
            # Process Frame
            # This handles detection, DB logging, and updating the Admin MJPEG stream
            annotated_img, _ = self.camera_service.process_frame_ndarray(img, self.session_id)
            
            # Convert back to WebRTC frame
            new_frame = av.VideoFrame.from_ndarray(annotated_img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
            
        except Exception as e:
            # If the track ends or errors, we log it
            # logger.error(f"WebRTC Frame Error: {e}")
            raise e
