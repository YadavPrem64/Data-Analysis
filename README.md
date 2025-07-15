# Data-Analysis

This repository contains two main components:

## 1. Data Analysis Project
This project, which focused on conducting an end-to-end data analysis process on a chosen dataset, was created using Google Colab. Data preprocessing, data cleaning, and feature handling were among the key steps in the workflow. Insightful visualizations were then created using a variety of Python libraries.

## 2. AI Guardian: Intelligent Streetlight & Surveillance Network

A complete AI-powered surveillance system designed for crime and emergency detection using modern Python technologies and beautiful UI design.

### Features

#### 🎯 Core Functionality
- **Real-time Object Detection**: Advanced AI detection using MediaPipe and YOLO models
- **Person & Vehicle Detection**: Accurate identification and tracking of people and vehicles
- **Suspicious Activity Analysis**: Intelligent behavior analysis for security monitoring
- **Crowd Detection**: Emergency situation detection for public safety
- **Multi-Camera Support**: Simultaneous monitoring of multiple camera feeds

#### 🎨 Modern Interface
- **Dark Theme UI**: Beautiful dark interface with neon blue accents using CustomTkinter
- **Real-time Feed Display**: Live camera feeds with detection overlays
- **Animated Status Indicators**: Professional status indicators with smooth animations
- **Detection Statistics**: Real-time statistics and performance monitoring
- **Alert Management**: Visual and audio alert notifications

#### 🔧 Technical Features
- **Multi-threading**: Smooth operation with optimized performance
- **Low-latency Processing**: Real-time detection with minimal delay
- **Memory Efficient**: Optimized for resource usage
- **Configurable Settings**: JSON-based configuration system
- **Alert Logging**: Comprehensive logging and history tracking

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YadavPrem64/Data-Analysis.git
   cd Data-Analysis
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

### System Requirements

- Python 3.8 or higher
- Camera/webcam for video input
- Minimum 4GB RAM (8GB recommended)
- GPU support optional but recommended for better performance

### Configuration

The system can be configured through `config/settings.json`:

- **Camera Settings**: Resolution, FPS, source selection
- **Detection Parameters**: Confidence thresholds, model selection
- **Alert Settings**: Audio/visual alert preferences
- **UI Configuration**: Theme, colors, window size

### Project Structure

```
ai-guardian/
├── main.py                    # Application entry point
├── src/
│   ├── ui/
│   │   └── dashboard.py      # Modern CustomTkinter interface
│   ├── detector/
│   │   └── ai_detector.py    # AI detection system
│   ├── alerts/
│   │   └── alert_manager.py  # Alert management
│   └── utils/
│       └── camera_manager.py # Camera operations
├── config/
│   └── settings.json         # Configuration file
├── assets/
│   └── sounds/              # Alert sound files
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Usage

1. **Start the Application**: Run `python main.py` to launch the dashboard
2. **Grant Camera Permissions**: Allow camera access when prompted
3. **Start Surveillance**: Click "START SURVEILLANCE" in the control panel
4. **Monitor Activity**: View real-time detection results and alerts
5. **Configure Settings**: Adjust detection sensitivity and alert preferences

### AI Detection Capabilities

- **Object Classes**: Person, Car, Truck, Motorcycle, Bicycle, and more
- **Suspicious Behavior**: Loitering, rapid movement, crowd formation
- **Weapon Detection**: Knife and gun detection for security alerts
- **Motion Analysis**: Advanced movement pattern recognition
- **Tracking**: Multi-object tracking with unique ID assignment

### Alert System

- **Visual Alerts**: Color-coded notifications with severity levels
- **Audio Alerts**: Configurable sound notifications
- **Emergency Protocols**: Escalation for critical situations
- **Alert History**: Complete logging with timestamps and details

### Performance

- **Real-time Processing**: 30 FPS video processing capability
- **Low CPU Usage**: Optimized algorithms for efficiency
- **GPU Acceleration**: Optional CUDA support for enhanced performance
- **Memory Management**: Intelligent resource usage optimization

### Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### License

This project is open source and available under the MIT License.
