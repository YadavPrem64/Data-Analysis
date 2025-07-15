"""
Alert Management System for AI Guardian

Handles visual alert notifications with animations, audio alerts using Pygame,
emergency response protocols, and alert logging and history.
"""

import pygame
import threading
import time
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import queue


@dataclass
class Alert:
    """Data class for alert information."""
    alert_id: str
    alert_type: str
    message: str
    severity: str  # low, medium, high, critical
    timestamp: datetime
    location: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolution_time:
            data['resolution_time'] = self.resolution_time.isoformat()
        return data


class AlertManager:
    """Manages visual and audio alerts for the surveillance system."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Alert Manager.
        
        Args:
            config: Alert configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Visual alert settings
        self.visual_config = config.get('visual', {})
        self.visual_enabled = self.visual_config.get('enabled', True)
        self.flash_duration = self.visual_config.get('flash_duration', 1.0)
        self.alert_colors = self.visual_config.get('colors', {
            'low': '#ffff00',
            'medium': '#ff8c00',
            'high': '#ff0000',
            'critical': '#8b0000'
        })
        
        # Audio alert settings
        self.audio_config = config.get('audio', {})
        self.audio_enabled = self.audio_config.get('enabled', True)
        self.volume = self.audio_config.get('volume', 0.7)
        self.sound_files = self.audio_config.get('sounds', {})
        
        # Logging settings
        self.logging_config = config.get('logging', {})
        self.logging_enabled = self.logging_config.get('enabled', True)
        self.log_file = self.logging_config.get('log_file', 'logs/alerts.log')
        
        # Alert storage and management
        self.active_alerts = {}
        self.alert_history = []
        self.alert_queue = queue.Queue()
        self.alert_callbacks = []
        
        # Threading and state
        self.processing_thread = None
        self.is_running = False
        self.alert_counter = 0
        
        # Initialize pygame for audio
        self.initialize_audio()
        
        # Setup logging
        self.setup_logging()
        
        # Start alert processing
        self.start_processing()
        
        self.logger.info("Alert Manager initialized")
    
    def initialize_audio(self):
        """Initialize pygame for audio alerts."""
        if not self.audio_enabled:
            return
        
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(8)  # Support multiple simultaneous sounds
            
            # Set volume
            pygame.mixer.music.set_volume(self.volume)
            
            # Load sound files
            self.loaded_sounds = {}
            for sound_type, sound_path in self.sound_files.items():
                if os.path.exists(sound_path):
                    try:
                        self.loaded_sounds[sound_type] = pygame.mixer.Sound(sound_path)
                        self.loaded_sounds[sound_type].set_volume(self.volume)
                        self.logger.info(f"Loaded sound: {sound_type} from {sound_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to load sound {sound_type}: {e}")
                else:
                    self.logger.warning(f"Sound file not found: {sound_path}")
            
            # Create default sounds if files not available
            if not self.loaded_sounds:
                self.create_default_sounds()
            
            self.logger.info("Audio system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio: {e}")
            self.audio_enabled = False
    
    def create_default_sounds(self):
        """Create simple default sounds using pygame."""
        try:
            # Create simple beep sounds
            sample_rate = 22050
            duration = 0.5
            
            # Detection sound (440 Hz)
            detection_samples = []
            for i in range(int(sample_rate * duration)):
                time_val = float(i) / sample_rate
                wave = 4096 * (0.5 * (1 + (time_val * 440 * 2)))
                detection_samples.append([int(wave), int(wave)])
            
            detection_sound = pygame.sndarray.make_sound(detection_samples)
            detection_sound.set_volume(self.volume * 0.5)
            self.loaded_sounds['detection'] = detection_sound
            
            # Alert sound (880 Hz)
            alert_samples = []
            for i in range(int(sample_rate * duration)):
                time_val = float(i) / sample_rate
                wave = 4096 * (0.5 * (1 + (time_val * 880 * 2)))
                alert_samples.append([int(wave), int(wave)])
            
            alert_sound = pygame.sndarray.make_sound(alert_samples)
            alert_sound.set_volume(self.volume * 0.7)
            self.loaded_sounds['alert'] = alert_sound
            
            # Emergency sound (1760 Hz)
            emergency_samples = []
            for i in range(int(sample_rate * duration)):
                time_val = float(i) / sample_rate
                wave = 4096 * (0.5 * (1 + (time_val * 1760 * 2)))
                emergency_samples.append([int(wave), int(wave)])
            
            emergency_sound = pygame.sndarray.make_sound(emergency_samples)
            emergency_sound.set_volume(self.volume)
            self.loaded_sounds['emergency'] = emergency_sound
            
            self.logger.info("Created default alert sounds")
            
        except Exception as e:
            self.logger.error(f"Failed to create default sounds: {e}")
    
    def setup_logging(self):
        """Setup alert logging."""
        if not self.logging_enabled:
            return
        
        try:
            # Create log directory
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Setup separate logger for alerts
            self.alert_logger = logging.getLogger('alerts')
            self.alert_logger.setLevel(logging.INFO)
            
            # Create file handler
            file_handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.alert_logger.addHandler(file_handler)
            
            self.logger.info(f"Alert logging initialized: {self.log_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup alert logging: {e}")
            self.logging_enabled = False
    
    def start_processing(self):
        """Start the alert processing thread."""
        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self._process_alerts,
            daemon=True
        )
        self.processing_thread.start()
        self.logger.info("Alert processing started")
    
    def _process_alerts(self):
        """Process alerts from the queue."""
        while self.is_running:
            try:
                # Get alert from queue with timeout
                alert = self.alert_queue.get(timeout=1.0)
                
                # Process the alert
                self._handle_alert(alert)
                
                # Mark task as done
                self.alert_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing alert: {e}")
    
    def _handle_alert(self, alert: Alert):
        """Handle individual alert processing."""
        try:
            # Add to active alerts
            self.active_alerts[alert.alert_id] = alert
            
            # Add to history
            self.alert_history.append(alert)
            
            # Trigger visual alert
            if self.visual_enabled:
                self._trigger_visual_alert(alert)
            
            # Trigger audio alert
            if self.audio_enabled:
                self._trigger_audio_alert(alert)
            
            # Log the alert
            if self.logging_enabled:
                self._log_alert(alert)
            
            # Notify callbacks
            self._notify_callbacks(alert)
            
            self.logger.info(f"Processed alert: {alert.alert_type} - {alert.message}")
            
        except Exception as e:
            self.logger.error(f"Error handling alert {alert.alert_id}: {e}")
    
    def _trigger_visual_alert(self, alert: Alert):
        """Trigger visual alert display."""
        try:
            # This would typically interface with the UI
            # For now, we'll just store the alert state
            color = self.alert_colors.get(alert.severity, '#ffffff')
            
            # Create visual alert info
            visual_alert = {
                'alert_id': alert.alert_id,
                'color': color,
                'flash_duration': self.flash_duration,
                'timestamp': alert.timestamp,
                'message': alert.message,
                'location': alert.location
            }
            
            # Store for UI access
            self.active_visual_alerts = getattr(self, 'active_visual_alerts', {})
            self.active_visual_alerts[alert.alert_id] = visual_alert
            
            # Auto-remove after flash duration
            def remove_visual_alert():
                time.sleep(self.flash_duration)
                if hasattr(self, 'active_visual_alerts') and alert.alert_id in self.active_visual_alerts:
                    del self.active_visual_alerts[alert.alert_id]
            
            threading.Thread(target=remove_visual_alert, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error triggering visual alert: {e}")
    
    def _trigger_audio_alert(self, alert: Alert):
        """Trigger audio alert playback."""
        try:
            # Determine sound type based on alert
            sound_type = 'detection'  # default
            
            if alert.severity in ['high', 'critical']:
                sound_type = 'emergency'
            elif alert.severity == 'medium':
                sound_type = 'alert'
            elif 'emergency' in alert.alert_type.lower():
                sound_type = 'emergency'
            elif 'suspicious' in alert.alert_type.lower():
                sound_type = 'alert'
            
            # Play sound
            if sound_type in self.loaded_sounds:
                sound = self.loaded_sounds[sound_type]
                
                # Play sound with repetition for critical alerts
                repetitions = 1
                if alert.severity == 'critical':
                    repetitions = 3
                elif alert.severity == 'high':
                    repetitions = 2
                
                def play_sound():
                    for _ in range(repetitions):
                        sound.play()
                        if repetitions > 1:
                            time.sleep(0.5)  # Short pause between repetitions
                
                threading.Thread(target=play_sound, daemon=True).start()
                
                self.logger.debug(f"Played {sound_type} sound for alert {alert.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Error triggering audio alert: {e}")
    
    def _log_alert(self, alert: Alert):
        """Log alert to file."""
        try:
            log_message = (
                f"ALERT - Type: {alert.alert_type}, "
                f"Severity: {alert.severity}, "
                f"Message: {alert.message}, "
                f"Confidence: {alert.confidence:.2f}"
            )
            
            if alert.location:
                log_message += f", Location: {alert.location}"
            
            self.alert_logger.info(log_message)
            
        except Exception as e:
            self.logger.error(f"Error logging alert: {e}")
    
    def _notify_callbacks(self, alert: Alert):
        """Notify registered callbacks about the alert."""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    def trigger_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = 'medium',
        location: Optional[Tuple[int, int]] = None,
        confidence: float = 0.0
    ) -> str:
        """
        Trigger a new alert.
        
        Args:
            alert_type: Type of alert (e.g., 'detection', 'suspicious_activity')
            message: Alert message
            severity: Alert severity ('low', 'medium', 'high', 'critical')
            location: Optional location coordinates
            confidence: Detection confidence (0.0 to 1.0)
            
        Returns:
            str: Alert ID
        """
        try:
            # Generate unique alert ID
            self.alert_counter += 1
            alert_id = f"{alert_type}_{int(time.time())}_{self.alert_counter}"
            
            # Create alert object
            alert = Alert(
                alert_id=alert_id,
                alert_type=alert_type,
                message=message,
                severity=severity,
                timestamp=datetime.now(),
                location=location,
                confidence=confidence
            )
            
            # Add to processing queue
            self.alert_queue.put(alert)
            
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Error triggering alert: {e}")
            return ""
    
    def resolve_alert(self, alert_id: str):
        """
        Resolve an active alert.
        
        Args:
            alert_id: ID of the alert to resolve
        """
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolution_time = datetime.now()
                
                # Remove from active alerts
                del self.active_alerts[alert_id]
                
                # Log resolution
                if self.logging_enabled:
                    self.alert_logger.info(f"RESOLVED - Alert {alert_id}")
                
                self.logger.info(f"Resolved alert: {alert_id}")
            
        except Exception as e:
            self.logger.error(f"Error resolving alert {alert_id}: {e}")
    
    def get_active_alerts(self) -> Dict[str, Alert]:
        """Get all active alerts."""
        return self.active_alerts.copy()
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        return self.alert_history[-limit:] if self.alert_history else []
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        try:
            stats = {
                'total_alerts': len(self.alert_history),
                'active_alerts': len(self.active_alerts),
                'alerts_by_type': {},
                'alerts_by_severity': {},
                'recent_alerts': len([a for a in self.alert_history if 
                                   (datetime.now() - a.timestamp).seconds < 3600])  # Last hour
            }
            
            # Count by type and severity
            for alert in self.alert_history:
                # Count by type
                if alert.alert_type in stats['alerts_by_type']:
                    stats['alerts_by_type'][alert.alert_type] += 1
                else:
                    stats['alerts_by_type'][alert.alert_type] = 1
                
                # Count by severity
                if alert.severity in stats['alerts_by_severity']:
                    stats['alerts_by_severity'][alert.severity] += 1
                else:
                    stats['alerts_by_severity'][alert.severity] = 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting alert stats: {e}")
            return {}
    
    def export_alerts(self, filename: str, start_date: Optional[datetime] = None):
        """
        Export alerts to JSON file.
        
        Args:
            filename: Output filename
            start_date: Optional start date filter
        """
        try:
            alerts_to_export = self.alert_history
            
            if start_date:
                alerts_to_export = [a for a in self.alert_history if a.timestamp >= start_date]
            
            # Convert to dictionaries
            export_data = [alert.to_dict() for alert in alerts_to_export]
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported {len(export_data)} alerts to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting alerts: {e}")
    
    def add_alert_callback(self, callback):
        """
        Add a callback function to be called when alerts are triggered.
        
        Args:
            callback: Function that takes an Alert object as parameter
        """
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback):
        """
        Remove an alert callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def set_volume(self, volume: float):
        """
        Set audio alert volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        
        if self.audio_enabled:
            try:
                pygame.mixer.music.set_volume(self.volume)
                
                # Update sound volume
                for sound in self.loaded_sounds.values():
                    sound.set_volume(self.volume)
                
                self.logger.info(f"Audio volume set to {self.volume}")
                
            except Exception as e:
                self.logger.error(f"Error setting volume: {e}")
    
    def toggle_audio(self, enabled: bool):
        """
        Enable or disable audio alerts.
        
        Args:
            enabled: Whether to enable audio alerts
        """
        self.audio_enabled = enabled
        self.logger.info(f"Audio alerts {'enabled' if enabled else 'disabled'}")
    
    def toggle_visual(self, enabled: bool):
        """
        Enable or disable visual alerts.
        
        Args:
            enabled: Whether to enable visual alerts
        """
        self.visual_enabled = enabled
        self.logger.info(f"Visual alerts {'enabled' if enabled else 'disabled'}")
    
    def cleanup(self):
        """Clean up alert manager resources."""
        self.logger.info("Cleaning up Alert Manager")
        
        # Stop processing
        self.is_running = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        
        # Stop audio
        if self.audio_enabled:
            try:
                pygame.mixer.quit()
            except Exception as e:
                self.logger.error(f"Error stopping audio: {e}")
        
        # Clear alerts
        self.active_alerts.clear()
        
        self.logger.info("Alert Manager cleanup complete")