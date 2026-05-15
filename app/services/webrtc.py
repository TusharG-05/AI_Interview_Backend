from aiortc import MediaStreamTrack
import av
import asyncio
import logging
import json
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Module-level thread pool for AI processing — avoids blocking the asyncio event loop
_ai_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="webrtc_ai")


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an input track.
    It applies Face & Gaze detection using the CameraService.
    Can optionally send real-time AI results over a WebRTC DataChannel.

    Fix: AI frame processing is now offloaded to a ThreadPoolExecutor so the
    asyncio event loop is never blocked by heavy OpenCV/MediaPipe work.
    """
    kind = "video"

    # Run AI analysis every N frames to keep the video smooth
    _AI_PROCESS_EVERY_N_FRAMES = 10

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
        self._ai_pending = False      # Guard: prevent overlapping AI jobs
        logger.info(f"WebRTC Track Initialized for Session: {interview_id} (DataChannel: {bool(channel)})")

    def _run_ai_sync(self, img):
        """
        Runs the heavy synchronous AI pipeline in a thread pool worker.
        This keeps the asyncio event loop unblocked.
        """
        return self.camera_service.process_frame_ndarray(img, self.interview_id)

    async def recv(self):
        try:
            frame = await self.track.recv()
            self.frame_count += 1

            # Only run heavy AI every N frames to keep the video smooth
            if self.frame_count % self._AI_PROCESS_EVERY_N_FRAMES == 0 and not self._ai_pending:
                # Convert WebRTC frame to numpy (BGR)
                img = frame.to_ndarray(format="bgr24")

                # FIX: Offload blocking AI work to thread pool instead of running synchronously.
                # This is the critical fix that prevents the asyncio event loop from freezing
                # when multiple candidates are connected simultaneously.
                self._ai_pending = True
                try:
                    loop = asyncio.get_event_loop()
                    annotated_img, results = await loop.run_in_executor(
                        _ai_executor, self._run_ai_sync, img
                    )
                finally:
                    self._ai_pending = False

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
