"""
Camera Manager for AI Guardian System

Handles camera initialization, video stream processing, frame capture,
and multi-camera support for the surveillance system.
"""

import cv2
import threading
import queue
import time
import logging
import numpy as np
from typing import Optional, Tuple, Dict, Any


class CameraManager:
    """Manages camera operations and video stream processing."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Camera Manager.
        
        Args:
            config: Camera configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Camera settings
        self.camera_source = config.get('default_source', 0)
        self.resolution = config.get('resolution', {'width': 640, 'height': 480})
        self.fps = config.get('fps', 30)
        self.buffer_size = config.get('buffer_size', 1)
        
        # Camera objects and state
        self.cameras = {}
        self.capture_threads = {}
        self.frame_queues = {}
        self.is_running = {}
        
        # Current frame storage
        self.current_frames = {}
        self.frame_locks = {}
        
        # Initialize primary camera
        self.initialize_camera(self.camera_source)
        
        self.logger.info("Camera Manager initialized")
    
    def initialize_camera(self, camera_id: int) -> bool:
        """
        Initialize a camera with the specified ID.
        
        Args:
            camera_id: Camera identifier (usually 0 for default camera)
            
        Returns:
            bool: True if camera initialized successfully, False otherwise
        """
        try:
            self.logger.info(f"Initializing camera {camera_id}")
            
            # Create camera capture object
            cap = cv2.VideoCapture(camera_id)
            
            if not cap.isOpened():
                self.logger.error(f"Failed to open camera {camera_id}")
                return False
            
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution['width'])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution['height'])
            cap.set(cv2.CAP_PROP_FPS, self.fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            
            # Enable auto exposure if configured
            if self.config.get('auto_exposure', True):
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            
            # Store camera objects
            self.cameras[camera_id] = cap
            self.frame_queues[camera_id] = queue.Queue(maxsize=2)
            self.current_frames[camera_id] = None
            self.frame_locks[camera_id] = threading.Lock()
            self.is_running[camera_id] = False
            
            # Test frame capture
            ret, frame = cap.read()
            if not ret:
                self.logger.error(f"Failed to capture test frame from camera {camera_id}")
                cap.release()
                return False
            
            self.logger.info(f"Camera {camera_id} initialized successfully - Resolution: {frame.shape[1]}x{frame.shape[0]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing camera {camera_id}: {e}")
            return False
    
    def start_capture(self, camera_id: int = None) -> bool:
        """
        Start video capture for the specified camera.
        
        Args:
            camera_id: Camera ID to start capture for (default: primary camera)
            
        Returns:
            bool: True if capture started successfully, False otherwise
        """
        if camera_id is None:
            camera_id = self.camera_source
        
        if camera_id not in self.cameras:
            self.logger.error(f"Camera {camera_id} not initialized")
            return False
        
        if self.is_running.get(camera_id, False):
            self.logger.warning(f"Camera {camera_id} capture already running")
            return True
        
        try:
            self.is_running[camera_id] = True
            
            # Create and start capture thread
            capture_thread = threading.Thread(
                target=self._capture_frames,
                args=(camera_id,),
                daemon=True
            )
            capture_thread.start()
            self.capture_threads[camera_id] = capture_thread
            
            self.logger.info(f"Started capture for camera {camera_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start capture for camera {camera_id}: {e}")
            self.is_running[camera_id] = False
            return False
    
    def _capture_frames(self, camera_id: int):
        """
        Continuously capture frames from the specified camera.
        
        Args:
            camera_id: Camera ID to capture frames from
        """
        cap = self.cameras[camera_id]
        frame_queue = self.frame_queues[camera_id]
        
        self.logger.info(f"Frame capture thread started for camera {camera_id}")
        
        while self.is_running.get(camera_id, False):
            try:
                ret, frame = cap.read()
                
                if not ret:
                    self.logger.warning(f"Failed to capture frame from camera {camera_id}")
                    time.sleep(0.1)
                    continue
                
                # Update current frame with thread safety
                with self.frame_locks[camera_id]:
                    self.current_frames[camera_id] = frame.copy()
                
                # Add frame to queue (non-blocking)
                try:
                    frame_queue.put_nowait(frame)
                except queue.Full:
                    # Remove old frame and add new one
                    try:
                        frame_queue.get_nowait()
                        frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                self.logger.error(f"Error in capture thread for camera {camera_id}: {e}")
                time.sleep(0.1)
        
        self.logger.info(f"Frame capture thread stopped for camera {camera_id}")
    
    def get_frame(self, camera_id: int = None) -> Optional[np.ndarray]:
        """
        Get the latest frame from the specified camera.
        
        Args:
            camera_id: Camera ID to get frame from (default: primary camera)
            
        Returns:
            numpy.ndarray: Latest frame or None if not available
        """
        if camera_id is None:
            camera_id = self.camera_source
        
        if camera_id not in self.current_frames:
            return None
        
        try:
            with self.frame_locks[camera_id]:
                if self.current_frames[camera_id] is not None:
                    return self.current_frames[camera_id].copy()
                else:
                    return None
        except Exception as e:
            self.logger.error(f"Error getting frame from camera {camera_id}: {e}")
            return None
    
    def get_frame_from_queue(self, camera_id: int = None, timeout: float = 0.1) -> Optional[np.ndarray]:
        """
        Get a frame from the camera's frame queue.
        
        Args:
            camera_id: Camera ID to get frame from (default: primary camera)
            timeout: Timeout in seconds to wait for frame
            
        Returns:
            numpy.ndarray: Frame from queue or None if not available
        """
        if camera_id is None:
            camera_id = self.camera_source
        
        if camera_id not in self.frame_queues:
            return None
        
        try:
            return self.frame_queues[camera_id].get(timeout=timeout)
        except queue.Empty:
            return None
        except Exception as e:
            self.logger.error(f"Error getting frame from queue for camera {camera_id}: {e}")
            return None
    
    def stop_capture(self, camera_id: int = None):
        """
        Stop video capture for the specified camera.
        
        Args:
            camera_id: Camera ID to stop capture for (default: primary camera)
        """
        if camera_id is None:
            camera_id = self.camera_source
        
        if camera_id in self.is_running:
            self.is_running[camera_id] = False
            
            # Wait for capture thread to finish
            if camera_id in self.capture_threads:
                self.capture_threads[camera_id].join(timeout=2.0)
                del self.capture_threads[camera_id]
            
            self.logger.info(f"Stopped capture for camera {camera_id}")
    
    def get_camera_info(self, camera_id: int = None) -> Dict[str, Any]:
        """
        Get information about the specified camera.
        
        Args:
            camera_id: Camera ID to get info for (default: primary camera)
            
        Returns:
            dict: Camera information
        """
        if camera_id is None:
            camera_id = self.camera_source
        
        if camera_id not in self.cameras:
            return {}
        
        cap = self.cameras[camera_id]
        
        try:
            info = {
                'camera_id': camera_id,
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'is_running': self.is_running.get(camera_id, False),
                'backend': cap.getBackendName()
            }
            return info
        except Exception as e:
            self.logger.error(f"Error getting camera info for camera {camera_id}: {e}")
            return {}
    
    def list_available_cameras(self, max_cameras: int = 10) -> list:
        """
        List all available cameras on the system.
        
        Args:
            max_cameras: Maximum number of cameras to check
            
        Returns:
            list: List of available camera IDs
        """
        available_cameras = []
        
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(i)
            cap.release()
        
        self.logger.info(f"Found {len(available_cameras)} available cameras: {available_cameras}")
        return available_cameras
    
    def add_camera(self, camera_id: int) -> bool:
        """
        Add a new camera to the system.
        
        Args:
            camera_id: Camera ID to add
            
        Returns:
            bool: True if camera added successfully, False otherwise
        """
        if camera_id in self.cameras:
            self.logger.warning(f"Camera {camera_id} already exists")
            return True
        
        return self.initialize_camera(camera_id)
    
    def remove_camera(self, camera_id: int):
        """
        Remove a camera from the system.
        
        Args:
            camera_id: Camera ID to remove
        """
        if camera_id not in self.cameras:
            return
        
        # Stop capture if running
        self.stop_capture(camera_id)
        
        # Release camera
        self.cameras[camera_id].release()
        
        # Clean up data structures
        del self.cameras[camera_id]
        if camera_id in self.frame_queues:
            del self.frame_queues[camera_id]
        if camera_id in self.current_frames:
            del self.current_frames[camera_id]
        if camera_id in self.frame_locks:
            del self.frame_locks[camera_id]
        if camera_id in self.is_running:
            del self.is_running[camera_id]
        
        self.logger.info(f"Removed camera {camera_id}")
    
    def cleanup(self):
        """Clean up all camera resources."""
        self.logger.info("Cleaning up Camera Manager")
        
        # Stop all captures
        for camera_id in list(self.cameras.keys()):
            self.stop_capture(camera_id)
            self.cameras[camera_id].release()
        
        # Clear all data structures
        self.cameras.clear()
        self.frame_queues.clear()
        self.current_frames.clear()
        self.frame_locks.clear()
        self.is_running.clear()
        self.capture_threads.clear()
        
        self.logger.info("Camera Manager cleanup complete")