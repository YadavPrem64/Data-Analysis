"""
Modern Dashboard for AI Guardian System

Beautiful dark-themed interface using CustomTkinter with real-time camera feed display,
live detection statistics and alerts, control panels for system management,
and status indicators with animations.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
from matplotlib.figure import Figure
import matplotlib.animation as animation


class AnimatedStatusIndicator(ctk.CTkFrame):
    """Animated status indicator widget."""
    
    def __init__(self, parent, status_text: str = "SYSTEM", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.status_text = status_text
        self.is_active = False
        self.animation_thread = None
        self.running = False
        
        # Create status label
        self.status_label = ctk.CTkLabel(
            self,
            text=self.status_text,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_label.pack(pady=5)
        
        # Create indicator circle
        self.indicator = ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color="gray"
        )
        self.indicator.pack()
    
    def start_animation(self, color: str = "#00ff00"):
        """Start the pulsing animation."""
        self.is_active = True
        self.running = True
        
        def animate():
            while self.running:
                try:
                    # Pulse effect
                    for alpha in [0.3, 0.7, 1.0, 0.7, 0.3]:
                        if not self.running:
                            break
                        
                        # Update color with alpha
                        self.indicator.configure(text_color=color)
                        time.sleep(0.2)
                    
                    time.sleep(0.5)
                    
                except Exception:
                    break
        
        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()
    
    def stop_animation(self):
        """Stop the animation."""
        self.running = False
        self.is_active = False
        self.indicator.configure(text_color="gray")
    
    def set_status(self, active: bool, color: str = "#00ff00"):
        """Set the status of the indicator."""
        if active and not self.is_active:
            self.start_animation(color)
        elif not active and self.is_active:
            self.stop_animation()


class CameraFeedWidget(ctk.CTkFrame):
    """Widget for displaying camera feed with detection overlays."""
    
    def __init__(self, parent, width: int = 640, height: int = 480, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.width = width
        self.height = height
        self.logger = logging.getLogger(__name__)
        
        # Create title
        self.title_label = ctk.CTkLabel(
            self,
            text="CAMERA FEED",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # Create canvas for video display
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg='black',
            highlightthickness=1,
            highlightbackground="#00bfff"
        )
        self.canvas.pack(padx=10, pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="NO SIGNAL",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        self.status_label.pack(pady=5)
        
        # Current frame
        self.current_frame = None
        self.frame_lock = threading.Lock()
    
    def update_frame(self, frame: np.ndarray):
        """Update the displayed frame."""
        try:
            with self.frame_lock:
                if frame is None:
                    self.status_label.configure(text="NO SIGNAL", text_color="red")
                    return
                
                # Resize frame to fit canvas
                frame_resized = cv2.resize(frame, (self.width, self.height))
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update canvas
                self.canvas.delete("all")
                self.canvas.create_image(
                    self.width // 2,
                    self.height // 2,
                    anchor=tk.CENTER,
                    image=photo
                )
                
                # Keep a reference to prevent garbage collection
                self.canvas.image = photo
                
                # Update status
                self.status_label.configure(text="LIVE", text_color="green")
                
        except Exception as e:
            self.logger.error(f"Error updating camera feed: {e}")
            self.status_label.configure(text="ERROR", text_color="red")


class DetectionStatsWidget(ctk.CTkFrame):
    """Widget for displaying detection statistics."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="DETECTION STATISTICS",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(10, 15))
        
        # Stats frame
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create stat labels
        self.stat_labels = {}
        self.create_stat_labels()
    
    def create_stat_labels(self):
        """Create labels for statistics display."""
        stats = [
            ("Total Detections", "total_detections"),
            ("FPS", "fps"),
            ("Tracked Objects", "tracked_objects"),
            ("Average Confidence", "confidence_avg")
        ]
        
        for i, (display_name, key) in enumerate(stats):
            # Label
            label = ctk.CTkLabel(
                self.stats_frame,
                text=f"{display_name}:",
                font=ctk.CTkFont(size=12)
            )
            label.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            
            # Value
            value_label = ctk.CTkLabel(
                self.stats_frame,
                text="0",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#00bfff"
            )
            value_label.grid(row=i, column=1, sticky="e", padx=10, pady=5)
            
            self.stat_labels[key] = value_label
        
        # Configure grid weights
        self.stats_frame.grid_columnconfigure(1, weight=1)
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update the displayed statistics."""
        try:
            for key, value in stats.items():
                if key in self.stat_labels:
                    if key == "fps":
                        display_value = f"{value:.1f}"
                    elif key == "confidence_avg":
                        display_value = f"{value:.2f}"
                    else:
                        display_value = str(value)
                    
                    self.stat_labels[key].configure(text=display_value)
            
            # Update classes detected
            if 'classes_detected' in stats:
                classes = stats['classes_detected']
                classes_text = ", ".join([f"{k}: {v}" for k, v in classes.items()])
                if hasattr(self, 'classes_label'):
                    self.classes_label.configure(text=classes_text[:50] + "..." if len(classes_text) > 50 else classes_text)
                else:
                    self.classes_label = ctk.CTkLabel(
                        self.stats_frame,
                        text=classes_text[:50] + "..." if len(classes_text) > 50 else classes_text,
                        font=ctk.CTkFont(size=10),
                        text_color="gray"
                    )
                    self.classes_label.grid(row=len(self.stat_labels), column=0, columnspan=2, padx=10, pady=5)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating stats: {e}")


class AlertsWidget(ctk.CTkFrame):
    """Widget for displaying active alerts and alert history."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="ALERTS & NOTIFICATIONS",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # Alert count
        self.alert_count_label = ctk.CTkLabel(
            self,
            text="Active Alerts: 0",
            font=ctk.CTkFont(size=12),
            text_color="#ff4444"
        )
        self.alert_count_label.pack(pady=5)
        
        # Scrollable frame for alerts
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            height=200,
            label_text="Recent Alerts"
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.alert_widgets = []
    
    def add_alert(self, alert_info: Dict[str, Any]):
        """Add a new alert to the display."""
        try:
            # Create alert frame
            alert_frame = ctk.CTkFrame(self.scrollable_frame)
            alert_frame.pack(fill="x", padx=5, pady=2)
            
            # Alert type and time
            header_text = f"{alert_info.get('alert_type', 'ALERT').upper()} - {alert_info.get('timestamp', datetime.now()).strftime('%H:%M:%S')}"
            header_label = ctk.CTkLabel(
                alert_frame,
                text=header_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=self.get_severity_color(alert_info.get('severity', 'medium'))
            )
            header_label.pack(anchor="w", padx=5, pady=2)
            
            # Alert message
            message_label = ctk.CTkLabel(
                alert_frame,
                text=alert_info.get('message', ''),
                font=ctk.CTkFont(size=9),
                wraplength=250
            )
            message_label.pack(anchor="w", padx=5, pady=1)
            
            # Keep only last 10 alerts
            self.alert_widgets.append(alert_frame)
            if len(self.alert_widgets) > 10:
                old_widget = self.alert_widgets.pop(0)
                old_widget.destroy()
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error adding alert: {e}")
    
    def get_severity_color(self, severity: str) -> str:
        """Get color based on alert severity."""
        colors = {
            'low': '#ffff00',
            'medium': '#ff8c00',
            'high': '#ff0000',
            'critical': '#8b0000'
        }
        return colors.get(severity, '#ffffff')
    
    def update_alert_count(self, count: int):
        """Update the active alert count."""
        self.alert_count_label.configure(text=f"Active Alerts: {count}")


class ControlPanelWidget(ctk.CTkFrame):
    """Widget for system control buttons and settings."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="SYSTEM CONTROLS",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(10, 15))
        
        # Control buttons frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # System control buttons
        self.start_button = ctk.CTkButton(
            self.controls_frame,
            text="START SURVEILLANCE",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#00aa00",
            hover_color="#00cc00",
            command=self.start_surveillance
        )
        self.start_button.pack(fill="x", padx=10, pady=5)
        
        self.stop_button = ctk.CTkButton(
            self.controls_frame,
            text="STOP SURVEILLANCE",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#aa0000",
            hover_color="#cc0000",
            command=self.stop_surveillance
        )
        self.stop_button.pack(fill="x", padx=10, pady=5)
        
        # Settings frame
        self.settings_frame = ctk.CTkFrame(self.controls_frame)
        self.settings_frame.pack(fill="x", padx=10, pady=10)
        
        # Audio toggle
        self.audio_toggle = ctk.CTkSwitch(
            self.settings_frame,
            text="Audio Alerts",
            command=self.toggle_audio
        )
        self.audio_toggle.pack(anchor="w", padx=10, pady=5)
        self.audio_toggle.select()  # Default on
        
        # Visual alerts toggle
        self.visual_toggle = ctk.CTkSwitch(
            self.settings_frame,
            text="Visual Alerts",
            command=self.toggle_visual
        )
        self.visual_toggle.pack(anchor="w", padx=10, pady=5)
        self.visual_toggle.select()  # Default on
        
        # Detection sensitivity slider
        self.sensitivity_label = ctk.CTkLabel(
            self.settings_frame,
            text="Detection Sensitivity",
            font=ctk.CTkFont(size=12)
        )
        self.sensitivity_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.sensitivity_slider = ctk.CTkSlider(
            self.settings_frame,
            from_=0.1,
            to=1.0,
            number_of_steps=9,
            command=self.update_sensitivity
        )
        self.sensitivity_slider.pack(fill="x", padx=10, pady=5)
        self.sensitivity_slider.set(0.5)  # Default value
        
        # Callbacks
        self.start_callback = None
        self.stop_callback = None
        self.audio_callback = None
        self.visual_callback = None
        self.sensitivity_callback = None
    
    def set_callbacks(self, start_cb=None, stop_cb=None, audio_cb=None, visual_cb=None, sensitivity_cb=None):
        """Set callback functions for control actions."""
        self.start_callback = start_cb
        self.stop_callback = stop_cb
        self.audio_callback = audio_cb
        self.visual_callback = visual_cb
        self.sensitivity_callback = sensitivity_cb
    
    def start_surveillance(self):
        """Start surveillance callback."""
        if self.start_callback:
            self.start_callback()
        
        # Update button states
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
    
    def stop_surveillance(self):
        """Stop surveillance callback."""
        if self.stop_callback:
            self.stop_callback()
        
        # Update button states
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
    
    def toggle_audio(self):
        """Toggle audio alerts."""
        if self.audio_callback:
            self.audio_callback(self.audio_toggle.get())
    
    def toggle_visual(self):
        """Toggle visual alerts."""
        if self.visual_callback:
            self.visual_callback(self.visual_toggle.get())
    
    def update_sensitivity(self, value):
        """Update detection sensitivity."""
        if self.sensitivity_callback:
            self.sensitivity_callback(float(value))


class Dashboard:
    """Main dashboard for AI Guardian surveillance system."""
    
    def __init__(self, config: Dict[str, Any], camera_manager, ai_detector, alert_manager):
        """
        Initialize the Dashboard.
        
        Args:
            config: Application configuration
            camera_manager: Camera manager instance
            ai_detector: AI detector instance
            alert_manager: Alert manager instance
        """
        self.config = config
        self.camera_manager = camera_manager
        self.ai_detector = ai_detector
        self.alert_manager = alert_manager
        self.logger = logging.getLogger(__name__)
        
        # UI configuration
        self.ui_config = config.get('ui', {})
        self.window_width = self.ui_config.get('window_width', 1400)
        self.window_height = self.ui_config.get('window_height', 900)
        self.accent_color = self.ui_config.get('accent_color', '#00bfff')
        
        # Application state
        self.is_surveillance_active = False
        self.update_thread = None
        self.running = False
        
        # Create main window
        self.create_main_window()
        
        # Setup alert callbacks
        self.setup_alert_callbacks()
        
        self.logger.info("Dashboard initialized")
    
    def create_main_window(self):
        """Create the main application window."""
        try:
            # Create main window
            self.root = ctk.CTk()
            self.root.title(self.config['app'].get('title', 'AI Guardian'))
            self.root.geometry(f"{self.window_width}x{self.window_height}")
            self.root.minsize(self.ui_config.get('min_width', 1200), self.ui_config.get('min_height', 800))
            
            # Configure grid weights
            self.root.grid_columnconfigure(1, weight=1)
            self.root.grid_rowconfigure(1, weight=1)
            
            # Create header
            self.create_header()
            
            # Create main content area
            self.create_main_content()
            
            # Create footer
            self.create_footer()
            
            self.logger.info("Main window created")
            
        except Exception as e:
            self.logger.error(f"Error creating main window: {e}")
            raise
    
    def create_header(self):
        """Create the header with title and status indicators."""
        header_frame = ctk.CTkFrame(self.root, height=80)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_propagate(False)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="AI GUARDIAN",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.accent_color
        )
        title_label.pack(side="left", padx=20, pady=20)
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Intelligent Streetlight & Surveillance Network",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(side="left", padx=(0, 20), pady=20)
        
        # Status indicators frame
        status_frame = ctk.CTkFrame(header_frame)
        status_frame.pack(side="right", padx=20, pady=10)
        
        # Create status indicators
        self.camera_status = AnimatedStatusIndicator(status_frame, "CAMERA")
        self.camera_status.pack(side="left", padx=5)
        
        self.ai_status = AnimatedStatusIndicator(status_frame, "AI")
        self.ai_status.pack(side="left", padx=5)
        
        self.alert_status = AnimatedStatusIndicator(status_frame, "ALERTS")
        self.alert_status.pack(side="left", padx=5)
    
    def create_main_content(self):
        """Create the main content area with camera feed and controls."""
        # Left panel for camera feed and stats
        left_panel = ctk.CTkFrame(self.root)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)
        left_panel.grid_rowconfigure(1, weight=1)
        
        # Camera feed
        self.camera_feed = CameraFeedWidget(left_panel, width=640, height=480)
        self.camera_feed.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Right panel for controls and alerts
        right_panel = ctk.CTkFrame(self.root)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)
        right_panel.grid_rowconfigure(2, weight=1)
        
        # Detection stats
        self.detection_stats = DetectionStatsWidget(right_panel)
        self.detection_stats.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Control panel
        self.control_panel = ControlPanelWidget(right_panel)
        self.control_panel.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Alerts widget
        self.alerts_widget = AlertsWidget(right_panel)
        self.alerts_widget.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # Configure control panel callbacks
        self.control_panel.set_callbacks(
            start_cb=self.start_surveillance,
            stop_cb=self.stop_surveillance,
            audio_cb=self.toggle_audio_alerts,
            visual_cb=self.toggle_visual_alerts,
            sensitivity_cb=self.update_detection_sensitivity
        )
    
    def create_footer(self):
        """Create the footer with system information."""
        footer_frame = ctk.CTkFrame(self.root, height=40)
        footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))
        footer_frame.grid_propagate(False)
        
        # System info
        version_text = f"AI Guardian v{self.config['app'].get('version', '1.0.0')}"
        version_label = ctk.CTkLabel(
            footer_frame,
            text=version_text,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack(side="left", padx=10, pady=10)
        
        # Current time
        self.time_label = ctk.CTkLabel(
            footer_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.time_label.pack(side="right", padx=10, pady=10)
        
        # Update time periodically
        self.update_time()
    
    def update_time(self):
        """Update the time display."""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.configure(text=current_time)
            self.root.after(1000, self.update_time)  # Update every second
        except Exception as e:
            self.logger.error(f"Error updating time: {e}")
    
    def setup_alert_callbacks(self):
        """Setup callbacks for alert notifications."""
        def alert_callback(alert):
            # Update alerts widget
            alert_info = {
                'alert_type': alert.alert_type,
                'message': alert.message,
                'severity': alert.severity,
                'timestamp': alert.timestamp
            }
            
            # Schedule UI update in main thread
            self.root.after(0, lambda: self.alerts_widget.add_alert(alert_info))
        
        self.alert_manager.add_alert_callback(alert_callback)
    
    def start_surveillance(self):
        """Start the surveillance system."""
        try:
            self.logger.info("Starting surveillance system")
            
            # Start camera capture
            if not self.camera_manager.start_capture():
                self.logger.error("Failed to start camera capture")
                return
            
            # Update status indicators
            self.camera_status.set_status(True, "#00ff00")
            self.ai_status.set_status(True, "#00ff00")
            self.alert_status.set_status(True, "#ffff00")
            
            # Start main update loop
            self.is_surveillance_active = True
            self.running = True
            self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
            self.update_thread.start()
            
            self.logger.info("Surveillance system started")
            
        except Exception as e:
            self.logger.error(f"Error starting surveillance: {e}")
    
    def stop_surveillance(self):
        """Stop the surveillance system."""
        try:
            self.logger.info("Stopping surveillance system")
            
            # Stop surveillance
            self.is_surveillance_active = False
            self.running = False
            
            # Stop camera capture
            self.camera_manager.stop_capture()
            
            # Update status indicators
            self.camera_status.set_status(False)
            self.ai_status.set_status(False)
            self.alert_status.set_status(False)
            
            self.logger.info("Surveillance system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping surveillance: {e}")
    
    def update_loop(self):
        """Main update loop for surveillance system."""
        while self.running:
            try:
                # Get frame from camera
                frame = self.camera_manager.get_frame()
                
                if frame is not None:
                    # Process frame with AI detector
                    detections, suspicious_activities = self.ai_detector.process_frame(frame)
                    
                    # Draw detections on frame
                    processed_frame = self.ai_detector.draw_detections(frame, detections)
                    
                    # Update camera feed in main thread
                    self.root.after(0, lambda: self.camera_feed.update_frame(processed_frame))
                    
                    # Get and update detection stats
                    stats = self.ai_detector.get_detection_stats()
                    self.root.after(0, lambda: self.detection_stats.update_stats(stats))
                    
                    # Update alert count
                    active_alerts = len(self.alert_manager.get_active_alerts())
                    self.root.after(0, lambda: self.alerts_widget.update_alert_count(active_alerts))
                
                # Control update rate
                time.sleep(1.0 / 30)  # 30 FPS
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                time.sleep(0.1)
    
    def toggle_audio_alerts(self, enabled: bool):
        """Toggle audio alerts on/off."""
        self.alert_manager.toggle_audio(enabled)
        self.logger.info(f"Audio alerts {'enabled' if enabled else 'disabled'}")
    
    def toggle_visual_alerts(self, enabled: bool):
        """Toggle visual alerts on/off."""
        self.alert_manager.toggle_visual(enabled)
        self.logger.info(f"Visual alerts {'enabled' if enabled else 'disabled'}")
    
    def update_detection_sensitivity(self, sensitivity: float):
        """Update detection sensitivity."""
        # Update AI detector confidence threshold
        self.ai_detector.confidence_threshold = sensitivity
        self.logger.info(f"Detection sensitivity updated to {sensitivity:.2f}")
    
    def run(self):
        """Start the dashboard application."""
        try:
            self.logger.info("Starting dashboard application")
            
            # Handle window close event
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Start the main loop
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            raise
    
    def on_closing(self):
        """Handle application closing."""
        try:
            self.logger.info("Dashboard closing")
            
            # Stop surveillance if active
            if self.is_surveillance_active:
                self.stop_surveillance()
            
            # Stop status animations
            if hasattr(self, 'camera_status'):
                self.camera_status.stop_animation()
            if hasattr(self, 'ai_status'):
                self.ai_status.stop_animation()
            if hasattr(self, 'alert_status'):
                self.alert_status.stop_animation()
            
            # Destroy window
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during closing: {e}")
    
    def cleanup(self):
        """Cleanup dashboard resources."""
        self.logger.info("Cleaning up Dashboard")
        
        # Stop surveillance
        if self.is_surveillance_active:
            self.stop_surveillance()
        
        # Wait for update thread to finish
        if self.update_thread:
            self.update_thread.join(timeout=2.0)
        
        self.logger.info("Dashboard cleanup complete")