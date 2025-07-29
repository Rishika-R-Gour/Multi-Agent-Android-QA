#!/usr/bin/env python3
"""
Android Studio Integration Test Script
Tests real device capabilities using Android Studio's emulator
"""

import subprocess
import time
import json
from datetime import datetime

class AndroidStudioTester:
    def __init__(self):
        self.adb_path = "/Users/rishikagour/Library/Android/sdk/platform-tools/adb"
        self.device_id = "emulator-5554"
        self.test_results = []
    
    def run_adb_command(self, command):
        """Execute ADB command and return output"""
        full_command = f"{self.adb_path} -s {self.device_id} {command}"
        try:
            result = subprocess.run(full_command.split(), capture_output=True, text=True, timeout=10)
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip()
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "Command timed out"}
    
    def test_device_connection(self):
        """Test basic device connection"""
        print("🔗 Testing device connection...")
        result = self.run_adb_command("shell echo 'Device connected'")
        
        test_result = {
            "test": "Device Connection",
            "success": result["success"],
            "details": result["output"] if result["success"] else result["error"],
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(test_result)
        
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {status}: {test_result['details']}")
        return result["success"]
    
    def test_device_info(self):
        """Get device information"""
        print("📱 Getting device information...")
        
        tests = [
            ("Android Version", "shell getprop ro.build.version.release"),
            ("Device Model", "shell getprop ro.product.model"),
            ("API Level", "shell getprop ro.build.version.sdk"),
            ("Screen Density", "shell wm density"),
            ("Screen Size", "shell wm size")
        ]
        
        device_info = {}
        for test_name, command in tests:
            result = self.run_adb_command(command)
            device_info[test_name] = result["output"] if result["success"] else "Unknown"
            
            test_result = {
                "test": f"Device Info - {test_name}",
                "success": result["success"],
                "details": result["output"],
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(test_result)
            
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {test_name}: {device_info[test_name]}")
        
        return device_info
    
    def test_app_operations(self):
        """Test app launching and navigation"""
        print("🚀 Testing app operations...")
        
        # Test Settings app launch
        print("   📱 Launching Settings app...")
        launch_result = self.run_adb_command("shell am start -a android.settings.SETTINGS")
        time.sleep(2)
        
        # Check current focus
        focus_result = self.run_adb_command("shell dumpsys window | grep mCurrentFocus")
        settings_launched = "com.android.settings" in focus_result.get("output", "")
        
        test_result = {
            "test": "Settings App Launch",
            "success": settings_launched,
            "details": focus_result["output"],
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(test_result)
        
        status = "✅ PASS" if settings_launched else "❌ FAIL"
        print(f"   {status}: Settings app launch")
        
        # Test WiFi settings navigation
        print("   📡 Navigating to WiFi settings...")
        wifi_result = self.run_adb_command("shell am start -a android.settings.WIFI_SETTINGS")
        time.sleep(2)
        
        focus_result = self.run_adb_command("shell dumpsys window | grep mCurrentFocus")
        wifi_opened = "WifiSettingsActivity" in focus_result.get("output", "")
        
        test_result = {
            "test": "WiFi Settings Navigation",
            "success": wifi_opened,
            "details": focus_result["output"],
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(test_result)
        
        status = "✅ PASS" if wifi_opened else "❌ FAIL"
        print(f"   {status}: WiFi settings navigation")
        
        return settings_launched and wifi_opened
    
    def test_ui_interactions(self):
        """Test UI interactions like taps and swipes"""
        print("👆 Testing UI interactions...")
        
        # Test screen tap
        tap_result = self.run_adb_command("shell input tap 540 1000")
        
        test_result = {
            "test": "Screen Tap",
            "success": tap_result["success"],
            "details": "Tap executed" if tap_result["success"] else tap_result["error"],
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(test_result)
        
        # Test text input
        text_result = self.run_adb_command("shell input text 'Test Input'")
        
        test_result = {
            "test": "Text Input",
            "success": text_result["success"],
            "details": "Text input executed" if text_result["success"] else text_result["error"],
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(test_result)
        
        # Test key press (back button)
        key_result = self.run_adb_command("shell input keyevent KEYCODE_BACK")
        
        test_result = {
            "test": "Key Press",
            "success": key_result["success"],
            "details": "Back key pressed" if key_result["success"] else key_result["error"],
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(test_result)
        
        interaction_success = all([tap_result["success"], text_result["success"], key_result["success"]])
        status = "✅ PASS" if interaction_success else "❌ FAIL"
        print(f"   {status}: UI interaction tests")
        
        return interaction_success
    
    def test_screenshot_capability(self):
        """Test screenshot functionality"""
        print("📸 Testing screenshot capability...")
        
        # Take screenshot
        screenshot_result = self.run_adb_command("shell screencap -p /sdcard/test_screenshot.png")
        
        if screenshot_result["success"]:
            # Pull screenshot
            pull_result = self.run_adb_command("pull /sdcard/test_screenshot.png ./android_studio_test_screenshot.png")
            success = pull_result["success"]
        else:
            success = False
        
        test_result = {
            "test": "Screenshot Capability",
            "success": success,
            "details": "Screenshot taken and pulled" if success else "Screenshot failed",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(test_result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: Screenshot capability")
        
        return success
    
    def run_qa_system_test(self):
        """Test integration with our QA system"""
        print("🤖 Testing QA system integration...")
        
        # Import our QA system
        try:
            import sys
            sys.path.append('/Users/rishikagour/QualGent_QA')
            from android_env_wrapper import AndroidEnv
            
            # Test AndroidEnv initialization
            env = AndroidEnv(task_name="android_studio_test", enable_real_device=True)
            
            # Test reset
            obs = env.reset()
            
            # Test step
            action = {"type": "tap", "target": "Settings"}
            result = env.step(action)
            
            test_result = {
                "test": "QA System Integration",
                "success": True,
                "details": f"AndroidEnv initialized, reset: {obs['status']}, step: {result['status']}",
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(test_result)
            
            print(f"   ✅ PASS: QA system integration working")
            return True
            
        except Exception as e:
            test_result = {
                "test": "QA System Integration",
                "success": False,
                "details": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(test_result)
            
            print(f"   ❌ FAIL: QA system integration - {str(e)}")
            return False
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating test report...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["success"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            "test_session": {
                "timestamp": datetime.now().isoformat(),
                "device_id": self.device_id,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate
            },
            "test_results": self.test_results
        }
        
        # Save JSON report
        with open('android_studio_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        markdown_report = f"""# Android Studio Integration Test Report

## Test Session Summary
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Device**: {self.device_id}
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {total_tests - passed_tests}
- **Success Rate**: {success_rate:.1f}%

## Test Results
"""
        
        for test in self.test_results:
            status = "✅ PASS" if test["success"] else "❌ FAIL"
            markdown_report += f"- **{test['test']}**: {status} - {test['details']}\n"
        
        with open('android_studio_test_report.md', 'w') as f:
            f.write(markdown_report)
        
        print(f"📋 Report saved: android_studio_test_report.json")
        print(f"📋 Report saved: android_studio_test_report.md")
        print(f"🎯 Overall Success Rate: {success_rate:.1f}%")
        
        return report
    
    def run_all_tests(self):
        """Run comprehensive Android Studio integration tests"""
        print("🚀 Starting Android Studio Integration Tests")
        print("=" * 60)
        
        # Run all test categories
        tests = [
            self.test_device_connection,
            self.test_device_info,
            self.test_app_operations,
            self.test_ui_interactions,
            self.test_screenshot_capability,
            self.run_qa_system_test
        ]
        
        overall_success = True
        for test_func in tests:
            try:
                result = test_func()
                if not result:
                    overall_success = False
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
                overall_success = False
        
        print("\n" + "=" * 60)
        final_status = "✅ ALL TESTS PASSED" if overall_success else "⚠️  SOME TESTS FAILED"
        print(f"{final_status}")
        
        # Generate comprehensive report
        report = self.generate_report()
        
        return report

if __name__ == "__main__":
    tester = AndroidStudioTester()
    report = tester.run_all_tests()
