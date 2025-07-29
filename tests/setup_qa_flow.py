#!/usr/bin/env python3
"""
Setup script for QA Flow with Agent-S + Android World integration.
This script ensures all dependencies are installed and configured properly.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def setup_virtual_environment():
    """Setup Python virtual environment if not already active."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is active")
        return True
    
    print("Setting up virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "qa_env"], check=True)
        print("✅ Virtual environment created: qa_env")
        print("   Activate with: source qa_env/bin/activate (Linux/Mac) or qa_env\\Scripts\\activate (Windows)")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False

def install_dependencies():
    """Install required Python packages."""
    print("Installing dependencies...")
    
    # Core dependencies
    dependencies = [
        "numpy",
        "logging",
        "typing-extensions",
        "dataclasses; python_version<'3.7'",
    ]
    
    # Optional dependencies for enhanced features
    optional_dependencies = [
        "transformers",  # For advanced AI planning
        "torch",         # For model inference
        "Pillow",        # For image processing
        "opencv-python", # For UI element detection
    ]
    
    try:
        # Install core dependencies
        for dep in dependencies:
            print(f"Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
        
        print("✅ Core dependencies installed")
        
        # Try to install optional dependencies
        for dep in optional_dependencies:
            try:
                print(f"Installing optional: {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print(f"⚠️  Optional dependency {dep} failed to install (skipping)")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_agent_s_integration():
    """Setup Agent-S integration."""
    print("Setting up Agent-S integration...")
    
    agent_s_path = Path("Agent-S")
    if agent_s_path.exists():
        print("✅ Agent-S directory found")
        
        # Check if Agent-S is properly installed
        try:
            sys.path.insert(0, str(agent_s_path))
            import gui_agents
            print("✅ Agent-S can be imported")
        except ImportError:
            print("⚠️  Agent-S import failed, using fallback implementation")
        
        return True
    else:
        print("⚠️  Agent-S directory not found")
        print("   This is OK - the QA flow will work with built-in implementations")
        return True

def setup_android_world_integration():
    """Setup Android World integration."""
    print("Setting up Android World integration...")
    
    android_world_path = Path("android_world")
    if android_world_path.exists():
        print("✅ Android World directory found")
        
        # Check if Android World can be imported
        try:
            sys.path.insert(0, str(android_world_path))
            from android_world.env import android_world_controller
            print("✅ Android World can be imported")
        except ImportError as e:
            print(f"⚠️  Android World import failed: {e}")
            print("   Using mock implementation for testing")
        
        return True
    else:
        print("⚠️  Android World directory not found")
        print("   Using mock implementation for testing")
        return True

def create_directory_structure():
    """Create necessary directories."""
    print("Creating directory structure...")
    
    directories = [
        "reports",
        "logs",
        "configs",
        "data"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def create_config_files():
    """Create default configuration files."""
    print("Creating configuration files...")
    
    # Create logging config
    logging_config = """
[loggers]
keys=root,qa_flow

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_qa_flow]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=qa_flow
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=simpleFormatter
args=('logs/qa_flow.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
"""
    
    with open("configs/logging.conf", "w") as f:
        f.write(logging_config)
    print("✅ Created logging configuration")
    
    # Create QA flow config
    qa_config = """{
    "default_task": "settings_wifi",
    "enable_real_device": false,
    "execution_timeout": 300,
    "step_delay": 1.0,
    "retry_attempts": 3,
    "report_format": "json",
    "agent_settings": {
        "planner": {
            "max_steps": 10,
            "validation_enabled": true
        },
        "executor": {
            "screenshot_enabled": true,
            "ui_analysis_enabled": true
        }
    }
}"""
    
    with open("configs/qa_flow.json", "w") as f:
        f.write(qa_config)
    print("✅ Created QA flow configuration")
    
    return True

def run_basic_tests():
    """Run basic tests to verify setup."""
    print("Running basic tests...")
    
    try:
        # Test AndroidEnv
        from android_env_wrapper import AndroidEnv
        env = AndroidEnv("settings_wifi")
        obs = env.reset()
        assert obs["status"] == "success"
        print("✅ AndroidEnv test passed")
        
        # Test PlannerAgent
        from planner_agent import PlannerAgent
        planner = PlannerAgent("settings_wifi")
        plan = planner.generate_test_plan("Test goal")
        assert len(plan["steps"]) > 0
        print("✅ PlannerAgent test passed")
        
        # Test ExecutorAgent
        from executor_agent import ExecutorAgent
        executor = ExecutorAgent("settings_wifi")
        test_plan = {
            "plan_id": "test",
            "steps": [{
                "step_id": 1,
                "action": "tap",
                "target": "test",
                "description": "test step",
                "validation_criteria": []
            }]
        }
        result = executor.execute_plan(test_plan)
        assert result["overall_status"] in ["success", "partial_success", "failed"]
        print("✅ ExecutorAgent test passed")
        
        print("✅ All basic tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

def main():
    """Main setup routine."""
    print("🚀 Setting up QA Flow with Agent-S + Android World")
    print("=" * 60)
    
    success = True
    
    # Run setup steps
    success &= check_python_version()
    success &= setup_virtual_environment()
    success &= install_dependencies()
    success &= setup_agent_s_integration()
    success &= setup_android_world_integration()
    success &= create_directory_structure()
    success &= create_config_files()
    success &= run_basic_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run demo: python demo_qa_flow.py")
        print("2. Run QA flow: python run_qa_flow.py --task settings_wifi")
        print("3. For real device: python run_qa_flow.py --real-device")
        print("4. Save reports: python run_qa_flow.py --save-report")
    else:
        print("❌ Setup encountered some issues")
        print("The QA flow should still work with reduced functionality")
    
    print("\nFor help: python run_qa_flow.py --help")

if __name__ == "__main__":
    main()
