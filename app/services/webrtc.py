from aiortc import MediaStreamTrack
import av
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an input track.
    It applies Face & Gaze detection using the CameraService.
    Can optionally send real-time AI results over a WebRTC DataChannel.
    """
    kind = "video"

    # Run AI analysis every N frames to avoid blocking the event loop
    _AI_PROCESS_EVERY_N_FRAMES = 5

    def __init__(self, track, interview_id: Optional[int] = None, channel=None):
        super().__init__()
        self.track = track
        from .camera import CameraService
        self.camera_service = CameraService()  # Singleton
        self.interview_id = interview_id
        self.channel = channel
        self.frame_count = 0
        self._last_results = {}       # Cache last known AI results
        self._last_annotated = None   # Cache last annotated frame
        logger.info(f"WebRTC Track Initialized for Session: {interview_id} (DataChannel: {bool(channel)})")

    async def recv(self):
        try:
            frame = await self.track.recv()
            self.frame_count += 1

            # Only run heavy AI every N frames to keep the video smooth
            if self.frame_count % self._AI_PROCESS_EVERY_N_FRAMES == 0:
                # Convert WebRTC frame to numpy (BGR)
                img = frame.to_ndarray(format="bgr24")

                # Process: detection + annotation + AI analysis (the heavy part)
                annotated_img, results = self.camera_service.process_frame_ndarray(img, self.interview_id)

                # Cache results for DataChannel pushes on non-AI frames
                self._last_results = results
                self._last_annotated = annotated_img

                output_frame = av.VideoFrame.from_ndarray(annotated_img, format="bgr24")
            else:
                # Pass the raw frame through immediately — no AI overhead
                output_frame = frame

            # Preserve original PTS and time_base for correct playback timing
            output_frame.pts = frame.pts
            output_frame.time_base = frame.time_base

            # PUSH TO DATA CHANNEL on AI frames (using cached results)
            if self._last_results and self.channel and self.channel.readyState == "open":
                try:
                    self.channel.send(json.dumps({
                        "type": "proctoring_update",
                        "interview_id": self.interview_id,
                        "data": self._last_results,
                        "frame_id": self.frame_count
                    }))
                except Exception as e:
                    logger.debug(f"DataChannel Send Error: {e}")

            return output_frame

        except Exception as e:
            logger.error(f"WebRTC: Frame Error Session {self.interview_id}: {e}")
            if 'frame' in locals():
                return frame
            raise
