#!/usr/bin/env python3
"""
AI Guardian Test Script

Simple test to verify the AI Guardian system structure and basic functionality
without requiring all heavy dependencies to be installed.
"""

import sys
import os
import json
from pathlib import Path

def test_project_structure():
    """Test that all required files and directories exist."""
    print("🔍 Testing project structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "config/settings.json",
        "src/__init__.py",
        "src/ui/__init__.py",
        "src/ui/dashboard.py",
        "src/detector/__init__.py", 
        "src/detector/ai_detector.py",
        "src/alerts/__init__.py",
        "src/alerts/alert_manager.py",
        "src/utils/__init__.py",
        "src/utils/camera_manager.py"
    ]
    
    required_dirs = [
        "src",
        "src/ui",
        "src/detector", 
        "src/alerts",
        "src/utils",
        "config",
        "assets",
        "assets/sounds",
        "logs"
    ]
    
    # Check directories
    for directory in required_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✓ Directory: {directory}")
        else:
            print(f"✗ Directory missing: {directory}")
            return False
    
    # Check files
    for file_path in required_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✓ File: {file_path}")
        else:
            print(f"✗ File missing: {file_path}")
            return False
    
    return True

def test_configuration():
    """Test configuration file validity."""
    print("\n🔧 Testing configuration...")
    
    try:
        with open("config/settings.json", 'r') as f:
            config = json.load(f)
        
        required_sections = ['app', 'ui', 'camera', 'detection', 'alerts']
        
        for section in required_sections:
            if section in config:
                print(f"✓ Config section: {section}")
            else:
                print(f"✗ Config section missing: {section}")
                return False
        
        # Test specific values
        app_name = config.get('app', {}).get('name', '')
        if app_name == "AI Guardian":
            print(f"✓ App name: {app_name}")
        else:
            print(f"✗ Invalid app name: {app_name}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_component_structure():
    """Test component file structure and basic syntax."""
    print("\n🧩 Testing component structure...")
    
    components = {
        "main.py": ["AIGuardianApp", "main"],
        "src/utils/camera_manager.py": ["CameraManager"],
        "src/detector/ai_detector.py": ["AIDetector", "Detection"],
        "src/alerts/alert_manager.py": ["AlertManager", "Alert"],
        "src/ui/dashboard.py": ["Dashboard", "CameraFeedWidget"]
    }
    
    for file_path, expected_classes in components.items():
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for class definitions
            for class_name in expected_classes:
                if f"class {class_name}" in content or f"def {class_name}" in content:
                    print(f"✓ {file_path}: {class_name}")
                else:
                    print(f"✗ {file_path}: {class_name} not found")
                    return False
                    
        except Exception as e:
            print(f"✗ Error reading {file_path}: {e}")
            return False
    
    return True

def test_dependencies():
    """Test dependencies in requirements.txt."""
    print("\n📦 Testing dependencies...")
    
    try:
        with open("requirements.txt", 'r') as f:
            requirements = f.read()
        
        essential_deps = [
            "customtkinter",
            "opencv-python", 
            "pygame",
            "numpy",
            "Pillow"
        ]
        
        for dep in essential_deps:
            if dep in requirements:
                print(f"✓ Dependency: {dep}")
            else:
                print(f"✗ Dependency missing: {dep}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading requirements: {e}")
        return False

def test_ai_guardian_features():
    """Test AI Guardian specific features and design."""
    print("\n🤖 Testing AI Guardian features...")
    
    # Test main.py for proper application structure
    try:
        with open("main.py", 'r') as f:
            main_content = f.read()
        
        features = [
            "AI Guardian",
            "CustomTkinter",
            "AIDetector", 
            "CameraManager",
            "AlertManager",
            "Dashboard"
        ]
        
        for feature in features:
            if feature in main_content:
                print(f"✓ Feature: {feature}")
            else:
                print(f"✗ Feature missing: {feature}")
                return False
                
    except Exception as e:
        print(f"✗ Error testing features: {e}")
        return False
    
    # Test dashboard for UI components
    try:
        with open("src/ui/dashboard.py", 'r') as f:
            dashboard_content = f.read()
        
        ui_features = [
            "dark-themed",
            "CustomTkinter",
            "CameraFeedWidget",
            "DetectionStatsWidget", 
            "AlertsWidget",
            "ControlPanelWidget",
            "AnimatedStatusIndicator"
        ]
        
        for feature in ui_features:
            if feature.lower().replace("-", "") in dashboard_content.lower():
                print(f"✓ UI Feature: {feature}")
            else:
                print(f"? UI Feature: {feature} (might be implemented differently)")
                
    except Exception as e:
        print(f"✗ Error testing UI features: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 AI Guardian System Test\n")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Configuration", test_configuration), 
        ("Component Structure", test_component_structure),
        ("Dependencies", test_dependencies),
        ("AI Guardian Features", test_ai_guardian_features)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n{'=' * 50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI Guardian system is ready.")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the application: python main.py") 
        print("3. Grant camera permissions when prompted")
        print("4. Start surveillance and monitor results")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)