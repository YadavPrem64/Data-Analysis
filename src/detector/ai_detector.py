"""
AI Detection System for AI Guardian

Provides real-time object detection using MediaPipe and YOLO models
for person detection, vehicle detection, suspicious activity analysis,
and crowd detection for emergency situations.
"""

import cv2
import numpy as np
import threading
import time
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Try to import detection libraries
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: MediaPipe not available. Some detection features may be limited.")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: YOLO not available. Using alternative detection methods.")


@dataclass
class Detection:
    """Data class for detection results."""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    timestamp: datetime
    track_id: Optional[int] = None


@dataclass
class SuspiciousActivity:
    """Data class for suspicious activity detection."""
    activity_type: str
    confidence: float
    location: Tuple[int, int]
    timestamp: datetime
    description: str


class AIDetector:
    """AI-powered detection system for surveillance applications."""
    
    def __init__(self, config: Dict[str, Any], alert_manager=None):
        """
        Initialize the AI Detector.
        
        Args:
            config: Detection configuration dictionary
            alert_manager: Alert manager instance for notifications
        """
        self.config = config
        self.alert_manager = alert_manager
        self.logger = logging.getLogger(__name__)
        
        # Detection settings
        self.model_type = config.get('model_type', 'yolo')
        self.confidence_threshold = config.get('confidence_threshold', 0.5)
        self.iou_threshold = config.get('iou_threshold', 0.45)
        self.max_detections = config.get('max_detections', 50)
        self.classes_of_interest = config.get('classes_of_interest', ['person', 'car'])
        
        # Suspicious activity settings
        self.suspicious_config = config.get('suspicious_activity', {})
        self.loitering_time = self.suspicious_config.get('loitering_time', 30)
        self.crowd_threshold = self.suspicious_config.get('crowd_threshold', 10)
        self.motion_sensitivity = self.suspicious_config.get('motion_sensitivity', 0.3)
        
        # Models and processors
        self.yolo_model = None
        self.mp_pose = None
        self.mp_hands = None
        self.mp_face_detection = None
        self.mp_drawing = None
        
        # Tracking data
        self.tracked_objects = {}
        self.person_tracks = {}
        self.motion_history = []
        self.crowd_areas = []
        
        # Processing state
        self.is_processing = False
        self.processing_thread = None
        self.frame_queue = []
        self.detection_results = []
        self.results_lock = threading.Lock()
        
        # Performance monitoring
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Initialize detection models
        self.initialize_models()
        
        self.logger.info("AI Detector initialized")
    
    def initialize_models(self):
        """Initialize AI detection models."""
        try:
            self.logger.info("Initializing AI detection models...")
            
            # Initialize YOLO model if available
            if YOLO_AVAILABLE and self.model_type.lower() == 'yolo':
                try:
                    model_path = self.config.get('model_path', 'yolov8n.pt')
                    self.yolo_model = YOLO(model_path)
                    self.logger.info(f"YOLO model loaded: {model_path}")
                except Exception as e:
                    self.logger.error(f"Failed to load YOLO model: {e}")
                    self.yolo_model = None
            
            # Initialize MediaPipe components if available
            if MEDIAPIPE_AVAILABLE:
                try:
                    self.mp_pose = mp.solutions.pose.Pose(
                        static_image_mode=False,
                        model_complexity=1,
                        enable_segmentation=False,
                        min_detection_confidence=0.5
                    )
                    
                    self.mp_hands = mp.solutions.hands.Hands(
                        static_image_mode=False,
                        max_num_hands=10,
                        min_detection_confidence=0.5
                    )
                    
                    self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
                        model_selection=0,
                        min_detection_confidence=0.5
                    )
                    
                    self.mp_drawing = mp.solutions.drawing_utils
                    
                    self.logger.info("MediaPipe models initialized")
                except Exception as e:
                    self.logger.error(f"Failed to initialize MediaPipe: {e}")
            
            # Fallback to OpenCV-based detection if no models available
            if not self.yolo_model and not MEDIAPIPE_AVAILABLE:
                self.logger.warning("No advanced AI models available, using OpenCV fallback")
                self.initialize_opencv_detectors()
            
        except Exception as e:
            self.logger.error(f"Error initializing models: {e}")
    
    def initialize_opencv_detectors(self):
        """Initialize OpenCV-based detectors as fallback."""
        try:
            # Initialize Haar cascades for basic detection
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.body_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_fullbody.xml'
            )
            
            # Background subtractor for motion detection
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True
            )
            
            self.logger.info("OpenCV detectors initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenCV detectors: {e}")
    
    def detect_objects(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect objects in the given frame.
        
        Args:
            frame: Input frame for detection
            
        Returns:
            List of Detection objects
        """
        detections = []
        
        try:
            # Use YOLO detection if available
            if self.yolo_model:
                detections.extend(self._yolo_detection(frame))
            
            # Use MediaPipe detection if available
            if MEDIAPIPE_AVAILABLE:
                detections.extend(self._mediapipe_detection(frame))
            
            # Fallback to OpenCV detection
            if not detections:
                detections.extend(self._opencv_detection(frame))
            
            # Filter detections by confidence and classes of interest
            filtered_detections = self._filter_detections(detections)
            
            # Update tracking
            self._update_tracking(filtered_detections)
            
            return filtered_detections
            
        except Exception as e:
            self.logger.error(f"Error in object detection: {e}")
            return []
    
    def _yolo_detection(self, frame: np.ndarray) -> List[Detection]:
        """Perform YOLO-based object detection."""
        detections = []
        
        try:
            # Run YOLO inference
            results = self.yolo_model(frame, conf=self.confidence_threshold, iou=self.iou_threshold)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box information
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Get class name
                        class_name = self.yolo_model.names[class_id]
                        
                        # Create detection object
                        detection = Detection(
                            class_name=class_name,
                            confidence=float(confidence),
                            bbox=(int(x1), int(y1), int(x2), int(y2)),
                            center=(int((x1 + x2) / 2), int((y1 + y2) / 2)),
                            timestamp=datetime.now()
                        )
                        
                        detections.append(detection)
            
        except Exception as e:
            self.logger.error(f"Error in YOLO detection: {e}")
        
        return detections
    
    def _mediapipe_detection(self, frame: np.ndarray) -> List[Detection]:
        """Perform MediaPipe-based detection."""
        detections = []
        
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]
            
            # Face detection
            if self.mp_face_detection:
                face_results = self.mp_face_detection.process(rgb_frame)
                if face_results.detections:
                    for detection in face_results.detections:
                        bbox = detection.location_data.relative_bounding_box
                        x1 = int(bbox.xmin * w)
                        y1 = int(bbox.ymin * h)
                        x2 = int((bbox.xmin + bbox.width) * w)
                        y2 = int((bbox.ymin + bbox.height) * h)
                        
                        det = Detection(
                            class_name='person',
                            confidence=detection.score[0],
                            bbox=(x1, y1, x2, y2),
                            center=(int((x1 + x2) / 2), int((y1 + y2) / 2)),
                            timestamp=datetime.now()
                        )
                        detections.append(det)
            
            # Pose detection
            if self.mp_pose:
                pose_results = self.mp_pose.process(rgb_frame)
                if pose_results.pose_landmarks:
                    # Extract bounding box from pose landmarks
                    landmarks = pose_results.pose_landmarks.landmark
                    x_coords = [lm.x * w for lm in landmarks]
                    y_coords = [lm.y * h for lm in landmarks]
                    
                    x1, y1 = int(min(x_coords)), int(min(y_coords))
                    x2, y2 = int(max(x_coords)), int(max(y_coords))
                    
                    # Add padding
                    padding = 20
                    x1 = max(0, x1 - padding)
                    y1 = max(0, y1 - padding)
                    x2 = min(w, x2 + padding)
                    y2 = min(h, y2 + padding)
                    
                    det = Detection(
                        class_name='person',
                        confidence=0.8,  # Pose detection confidence
                        bbox=(x1, y1, x2, y2),
                        center=(int((x1 + x2) / 2), int((y1 + y2) / 2)),
                        timestamp=datetime.now()
                    )
                    detections.append(det)
            
        except Exception as e:
            self.logger.error(f"Error in MediaPipe detection: {e}")
        
        return detections
    
    def _opencv_detection(self, frame: np.ndarray) -> List[Detection]:
        """Perform OpenCV-based detection as fallback."""
        detections = []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Face detection
            if hasattr(self, 'face_cascade'):
                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                
                for (x, y, w, h) in faces:
                    det = Detection(
                        class_name='person',
                        confidence=0.7,
                        bbox=(x, y, x + w, y + h),
                        center=(x + w // 2, y + h // 2),
                        timestamp=datetime.now()
                    )
                    detections.append(det)
            
            # Motion detection
            if hasattr(self, 'bg_subtractor'):
                fg_mask = self.bg_subtractor.apply(frame)
                contours, _ = cv2.findContours(
                    fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 500:  # Minimum area threshold
                        x, y, w, h = cv2.boundingRect(contour)
                        det = Detection(
                            class_name='motion',
                            confidence=0.6,
                            bbox=(x, y, x + w, y + h),
                            center=(x + w // 2, y + h // 2),
                            timestamp=datetime.now()
                        )
                        detections.append(det)
            
        except Exception as e:
            self.logger.error(f"Error in OpenCV detection: {e}")
        
        return detections
    
    def _filter_detections(self, detections: List[Detection]) -> List[Detection]:
        """Filter detections based on confidence and classes of interest."""
        filtered = []
        
        for detection in detections:
            # Check confidence threshold
            if detection.confidence < self.confidence_threshold:
                continue
            
            # Check if class is of interest
            if self.classes_of_interest and detection.class_name not in self.classes_of_interest:
                continue
            
            filtered.append(detection)
        
        # Limit number of detections
        if len(filtered) > self.max_detections:
            filtered = sorted(filtered, key=lambda x: x.confidence, reverse=True)[:self.max_detections]
        
        return filtered
    
    def _update_tracking(self, detections: List[Detection]):
        """Update object tracking information."""
        try:
            current_time = time.time()
            
            # Simple tracking based on distance
            for detection in detections:
                best_match = None
                min_distance = float('inf')
                
                # Find closest existing track
                for track_id, track_info in self.tracked_objects.items():
                    if track_info['class'] == detection.class_name:
                        distance = np.sqrt(
                            (detection.center[0] - track_info['last_center'][0]) ** 2 +
                            (detection.center[1] - track_info['last_center'][1]) ** 2
                        )
                        
                        if distance < min_distance and distance < 100:  # Distance threshold
                            min_distance = distance
                            best_match = track_id
                
                if best_match:
                    # Update existing track
                    self.tracked_objects[best_match].update({
                        'last_center': detection.center,
                        'last_seen': current_time,
                        'confidence': detection.confidence
                    })
                    detection.track_id = best_match
                else:
                    # Create new track
                    new_track_id = len(self.tracked_objects) + 1
                    self.tracked_objects[new_track_id] = {
                        'class': detection.class_name,
                        'first_seen': current_time,
                        'last_seen': current_time,
                        'last_center': detection.center,
                        'confidence': detection.confidence
                    }
                    detection.track_id = new_track_id
            
            # Remove old tracks
            tracks_to_remove = []
            for track_id, track_info in self.tracked_objects.items():
                if current_time - track_info['last_seen'] > 5.0:  # 5 second timeout
                    tracks_to_remove.append(track_id)
            
            for track_id in tracks_to_remove:
                del self.tracked_objects[track_id]
            
        except Exception as e:
            self.logger.error(f"Error updating tracking: {e}")
    
    def detect_suspicious_activity(self, detections: List[Detection], frame: np.ndarray) -> List[SuspiciousActivity]:
        """Detect suspicious activities based on detection results."""
        suspicious_activities = []
        
        try:
            current_time = time.time()
            
            # Check for loitering (person staying in same area)
            person_detections = [d for d in detections if d.class_name == 'person']
            
            for detection in person_detections:
                if detection.track_id:
                    track_info = self.tracked_objects.get(detection.track_id)
                    if track_info:
                        duration = current_time - track_info['first_seen']
                        if duration > self.loitering_time:
                            activity = SuspiciousActivity(
                                activity_type='loitering',
                                confidence=0.8,
                                location=detection.center,
                                timestamp=datetime.now(),
                                description=f'Person loitering for {duration:.1f} seconds'
                            )
                            suspicious_activities.append(activity)
            
            # Check for crowd formation
            if len(person_detections) >= self.crowd_threshold:
                # Calculate center of crowd
                centers = [d.center for d in person_detections]
                crowd_center = (
                    sum(c[0] for c in centers) // len(centers),
                    sum(c[1] for c in centers) // len(centers)
                )
                
                activity = SuspiciousActivity(
                    activity_type='crowd_detected',
                    confidence=0.9,
                    location=crowd_center,
                    timestamp=datetime.now(),
                    description=f'Crowd of {len(person_detections)} people detected'
                )
                suspicious_activities.append(activity)
            
            # Check for rapid movement (potential chase or escape)
            for detection in person_detections:
                if detection.track_id:
                    track_info = self.tracked_objects.get(detection.track_id)
                    if track_info and 'movement_history' in track_info:
                        # Calculate movement speed
                        history = track_info['movement_history']
                        if len(history) > 2:
                            recent_positions = history[-3:]
                            total_distance = sum(
                                np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                                for p1, p2 in zip(recent_positions[:-1], recent_positions[1:])
                            )
                            
                            if total_distance > 200:  # High movement threshold
                                activity = SuspiciousActivity(
                                    activity_type='rapid_movement',
                                    confidence=0.7,
                                    location=detection.center,
                                    timestamp=datetime.now(),
                                    description='Rapid movement detected'
                                )
                                suspicious_activities.append(activity)
            
            # Send alerts for suspicious activities
            for activity in suspicious_activities:
                if self.alert_manager:
                    self.alert_manager.trigger_alert(
                        alert_type='suspicious_activity',
                        message=activity.description,
                        location=activity.location,
                        confidence=activity.confidence
                    )
            
        except Exception as e:
            self.logger.error(f"Error detecting suspicious activity: {e}")
        
        return suspicious_activities
    
    def process_frame(self, frame: np.ndarray) -> Tuple[List[Detection], List[SuspiciousActivity]]:
        """
        Process a single frame and return detection results.
        
        Args:
            frame: Input frame to process
            
        Returns:
            Tuple of (detections, suspicious_activities)
        """
        try:
            # Perform object detection
            detections = self.detect_objects(frame)
            
            # Detect suspicious activities
            suspicious_activities = self.detect_suspicious_activity(detections, frame)
            
            # Update FPS counter
            self.fps_counter += 1
            current_time = time.time()
            if current_time - self.fps_start_time >= 1.0:
                self.current_fps = self.fps_counter
                self.fps_counter = 0
                self.fps_start_time = current_time
            
            # Store results
            with self.results_lock:
                self.detection_results = detections
            
            return detections, suspicious_activities
            
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            return [], []
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Draw detection results on the frame.
        
        Args:
            frame: Input frame
            detections: List of detections to draw
            
        Returns:
            Frame with drawn detections
        """
        try:
            output_frame = frame.copy()
            
            for detection in detections:
                x1, y1, x2, y2 = detection.bbox
                
                # Choose color based on class
                if detection.class_name == 'person':
                    color = (0, 255, 0)  # Green for person
                elif detection.class_name in ['car', 'truck', 'motorcycle']:
                    color = (255, 0, 0)  # Blue for vehicles
                elif detection.class_name in ['knife', 'gun']:
                    color = (0, 0, 255)  # Red for weapons
                else:
                    color = (255, 255, 0)  # Cyan for others
                
                # Draw bounding box
                cv2.rectangle(output_frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{detection.class_name}: {detection.confidence:.2f}"
                if detection.track_id:
                    label += f" ID:{detection.track_id}"
                
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(
                    output_frame,
                    (x1, y1 - label_size[1] - 10),
                    (x1 + label_size[0], y1),
                    color,
                    -1
                )
                cv2.putText(
                    output_frame,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
            
            # Draw FPS counter
            cv2.putText(
                output_frame,
                f"FPS: {self.current_fps}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )
            
            # Draw detection count
            cv2.putText(
                output_frame,
                f"Detections: {len(detections)}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )
            
            return output_frame
            
        except Exception as e:
            self.logger.error(f"Error drawing detections: {e}")
            return frame
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        with self.results_lock:
            detections = self.detection_results.copy()
        
        stats = {
            'total_detections': len(detections),
            'fps': self.current_fps,
            'tracked_objects': len(self.tracked_objects),
            'classes_detected': {},
            'confidence_avg': 0.0
        }
        
        if detections:
            # Count classes
            for detection in detections:
                if detection.class_name in stats['classes_detected']:
                    stats['classes_detected'][detection.class_name] += 1
                else:
                    stats['classes_detected'][detection.class_name] = 1
            
            # Calculate average confidence
            stats['confidence_avg'] = sum(d.confidence for d in detections) / len(detections)
        
        return stats
    
    def cleanup(self):
        """Clean up AI detector resources."""
        self.logger.info("Cleaning up AI Detector")
        
        self.is_processing = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        
        # Clean up MediaPipe resources
        if self.mp_pose:
            self.mp_pose.close()
        if self.mp_hands:
            self.mp_hands.close()
        if self.mp_face_detection:
            self.mp_face_detection.close()
        
        self.logger.info("AI Detector cleanup complete")