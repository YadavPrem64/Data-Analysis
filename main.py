#!/usr/bin/env python3
"""
AI Guardian: Intelligent Streetlight & Surveillance Network
Main Application Entry Point

This application provides real-time surveillance capabilities with AI-powered
detection for enhanced security and emergency response.

Author: AI Guardian Team
Version: 1.0.0
"""

import sys
import os
import json
import logging
import traceback
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import customtkinter as ctk
    from src.ui.dashboard import Dashboard
    from src.utils.camera_manager import CameraManager
    from src.detector.ai_detector import AIDetector
    from src.alerts.alert_manager import AlertManager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install the required dependencies using: pip install -r requirements.txt")
    sys.exit(1)


class AIGuardianApp:
    """Main application class for AI Guardian surveillance system."""
    
    def __init__(self):
        """Initialize the AI Guardian application."""
        self.config = self.load_config()
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.camera_manager = None
        self.ai_detector = None
        self.alert_manager = None
        self.dashboard = None
        
        self.logger.info("AI Guardian application initialized")
    
    def load_config(self):
        """Load application configuration from settings.json."""
        config_path = Path(__file__).parent / "config" / "settings.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file not found: {config_path}")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration if config file is not available."""
        return {
            "app": {"name": "AI Guardian", "version": "1.0.0"},
            "ui": {"theme": "dark", "accent_color": "#00bfff", "window_width": 1400, "window_height": 900},
            "camera": {"default_source": 0, "resolution": {"width": 640, "height": 480}, "fps": 30},
            "detection": {"confidence_threshold": 0.5, "classes_of_interest": ["person", "car"]},
            "alerts": {"visual": {"enabled": True}, "audio": {"enabled": True}}
        }
    
    def setup_logging(self):
        """Set up logging configuration."""
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "ai_guardian.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def initialize_components(self):
        """Initialize all application components."""
        try:
            self.logger.info("Initializing application components...")
            
            # Initialize Alert Manager first
            self.alert_manager = AlertManager(self.config.get('alerts', {}))
            
            # Initialize Camera Manager
            self.camera_manager = CameraManager(self.config.get('camera', {}))
            
            # Initialize AI Detector
            self.ai_detector = AIDetector(
                self.config.get('detection', {}),
                self.alert_manager
            )
            
            # Initialize Dashboard (UI)
            self.dashboard = Dashboard(
                self.config,
                self.camera_manager,
                self.ai_detector,
                self.alert_manager
            )
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def run(self):
        """Start the AI Guardian application."""
        try:
            self.logger.info("Starting AI Guardian application...")
            
            # Set CustomTkinter appearance mode and color theme
            ctk.set_appearance_mode(self.config['ui'].get('theme', 'dark'))
            ctk.set_default_color_theme("blue")
            
            # Initialize all components
            self.initialize_components()
            
            # Start the dashboard
            self.dashboard.run()
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
            self.shutdown()
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            self.logger.error(traceback.format_exc())
            self.shutdown()
            sys.exit(1)
    
    def shutdown(self):
        """Cleanup and shutdown the application."""
        self.logger.info("Shutting down AI Guardian application...")
        
        try:
            if self.camera_manager:
                self.camera_manager.cleanup()
            
            if self.ai_detector:
                self.ai_detector.cleanup()
            
            if self.alert_manager:
                self.alert_manager.cleanup()
            
            if self.dashboard:
                self.dashboard.cleanup()
                
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        self.logger.info("Application shutdown complete")


def main():
    """Main entry point of the application."""
    try:
        # Create and run the application
        app = AIGuardianApp()
        app.run()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()