try:
    from android_world.env import android_world_controller
    from android_world.env import interface
    ANDROID_WORLD_AVAILABLE = True
except ImportError:
    # Android World not available, use mock implementation
    android_world_controller = None
    interface = None
    ANDROID_WORLD_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    # Create mock numpy for basic functionality
    NUMPY_AVAILABLE = False
    class MockNumpy:
        @property
        def uint8(self):
            return "uint8"
            
        def zeros(self, shape, dtype=None):
            # Return a simple list representation for mock screenshot
            if len(shape) == 3:
                return [[[0 for _ in range(shape[2])] for _ in range(shape[1])] for _ in range(shape[0])]
            return [[0 for _ in range(shape[1])] for _ in range(shape[0])]
    np = MockNumpy()

from typing import Dict, Any, Optional
import logging

class DummyEnv:
    """Minimal environment placeholder just to satisfy the controller."""
    def __init__(self, task_name):
        self.task_name = task_name

class AndroidEnv:
    """Enhanced wrapper that integrates AndroidWorld with Agent-S messaging structure."""
    
    def __init__(self, task_name="settings_wifi", enable_real_device=False):
        self.task_name = task_name
        self.enable_real_device = enable_real_device and ANDROID_WORLD_AVAILABLE
        self.logger = logging.getLogger(f"AndroidEnv.{task_name}")
        
        if self.enable_real_device and android_world_controller:
            # Initialize real AndroidWorld controller
            dummy_env = DummyEnv(task_name)
            self.controller = android_world_controller.AndroidWorldController(dummy_env)
        else:
            # Mock mode for testing
            self.controller = None
            if enable_real_device and not ANDROID_WORLD_AVAILABLE:
                self.logger.warning("Real device requested but Android World not available. Using mock mode.")
            
        self.current_state = None
        self.step_count = 0

    def reset(self) -> Dict[str, Any]:
        """Reset environment and return initial observation."""
        self.step_count = 0
        
        if self.enable_real_device and self.controller:
            try:
                # Real AndroidWorld reset
                state = self.controller.get_state()
                self.current_state = state
                return {
                    "status": "success",
                    "task_name": self.task_name,
                    "state": state,
                    "pixels": state.pixels if hasattr(state, 'pixels') else None,
                    "ui_elements": state.ui_elements if hasattr(state, 'ui_elements') else []
                }
            except Exception as e:
                self.logger.error(f"Real device reset failed: {e}")
                return self._mock_reset()
        else:
            return self._mock_reset()

    def _mock_reset(self) -> Dict[str, Any]:
        """Mock reset for testing without real device."""
        return {
            "status": "success", 
            "task_name": self.task_name,
            "message": f"Mock environment for {self.task_name} initialized",
            "ui_elements": [
                {"text": "Settings", "bounds": [0, 0, 100, 50], "clickable": True},
                {"text": "Wi-Fi", "bounds": [0, 100, 100, 150], "clickable": True}
            ],
            "pixels": np.zeros((1080, 1920, 3), dtype=np.uint8)  # Mock screenshot
        }

    def get_state(self) -> Dict[str, Any]:
        """Get current environment state."""
        if self.enable_real_device and self.controller:
            try:
                # Real AndroidWorld state
                state = self.controller.get_state()
                self.current_state = state
                return {
                    "status": "success",
                    "state": state,
                    "pixels": state.pixels if hasattr(state, 'pixels') else None,
                    "ui_elements": state.ui_elements if hasattr(state, 'ui_elements') else []
                }
            except Exception as e:
                self.logger.error(f"Real get_state failed: {e}")
                return self._mock_get_state()
        else:
            return self._mock_get_state()
    
    def _mock_get_state(self) -> Dict[str, Any]:
        """Mock get state for testing."""
        return {
            "status": "success",
            "ui_elements": [
                {"text": "Settings", "bounds": [0, 0, 100, 50], "clickable": True},
                {"text": "Wi-Fi", "bounds": [0, 100, 100, 150], "clickable": True},
                {"text": "ON", "bounds": [350, 100, 400, 150], "clickable": True, "switch": True}
            ],
            "pixels": np.zeros((1080, 1920, 3), dtype=np.uint8) if NUMPY_AVAILABLE else None
        }

    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action and return new observation."""
        self.step_count += 1
        
        if self.enable_real_device and self.controller:
            return self._real_step(action)
        else:
            return self._mock_step(action)

    def _real_step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute real action on AndroidWorld."""
        try:
            # Convert high-level action to AndroidWorld format
            android_action = self._convert_action(action)
            
            # Execute action
            result = self.controller.step(android_action)
            
            # Get new state
            new_state = self.controller.get_state()
            self.current_state = new_state
            
            return {
                "status": "success",
                "step": self.step_count,
                "action_executed": action,
                "state": new_state,
                "pixels": new_state.pixels if hasattr(new_state, 'pixels') else None,
                "ui_elements": new_state.ui_elements if hasattr(new_state, 'ui_elements') else []
            }
        except Exception as e:
            self.logger.error(f"Real step failed: {e}")
            return self._mock_step(action)

    def _mock_step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Mock action execution for testing."""
        action_type = action.get("action_type", "unknown")
        element_id = action.get("element_id", "unknown")
        target = action.get("target", "unknown")
        coordinates = action.get("coordinates", [500, 500])
        
        # Simulate different UI states based on action
        mock_ui_elements = []
        
        # Handle different action types with grounded element responses
        if action_type == "touch":
            if "settings" in target.lower():
                mock_ui_elements = [
                    {"text": "Network & internet", "bounds": [0, 100, 400, 150], "clickable": True},
                    {"text": "Connected devices", "bounds": [0, 150, 400, 200], "clickable": True},
                    {"text": "Apps", "bounds": [0, 200, 400, 250], "clickable": True}
                ]
            elif "wifi" in target.lower() or "wi-fi" in target.lower():
                mock_ui_elements = [
                    {"text": "Wi-Fi", "bounds": [0, 50, 100, 100], "clickable": False},
                    {"text": "OFF", "bounds": [350, 50, 400, 100], "clickable": True, "switch": True},
                    {"text": "Available networks", "bounds": [0, 150, 400, 200], "clickable": False}
                ]
            elif "network" in target.lower():
                mock_ui_elements = [
                    {"text": "Wi-Fi", "bounds": [0, 100, 400, 150], "clickable": True},
                    {"text": "Mobile network", "bounds": [0, 150, 400, 200], "clickable": True},
                    {"text": "Hotspot & tethering", "bounds": [0, 200, 400, 250], "clickable": True}
                ]
            elif "off" in target.lower() or "on" in target.lower():
                # Toggle action - switch the state
                new_state = "ON" if "off" in target.lower() else "OFF"
                mock_ui_elements = [
                    {"text": "Wi-Fi", "bounds": [0, 50, 100, 100], "clickable": False},
                    {"text": new_state, "bounds": [350, 50, 400, 100], "clickable": True, "switch": True},
                    {"text": "Available networks", "bounds": [0, 150, 400, 200], "clickable": False}
                ]
        
        elif action_type == "type":
            mock_ui_elements = [
                {"text": "Search box (active)", "bounds": [0, 50, 400, 100], "clickable": True},
                {"text": "Keyboard", "bounds": [0, 400, 400, 600], "clickable": False}
            ]
        
        elif action_type == "inspect":
            # Return current UI state for inspection
            mock_ui_elements = [
                {"text": "Settings", "bounds": [0, 0, 100, 50], "clickable": True},
                {"text": "Wi-Fi", "bounds": [0, 100, 100, 150], "clickable": True},
                {"text": "OFF", "bounds": [350, 100, 400, 150], "clickable": True}
            ]
        
        # Default elements if none specified
        if not mock_ui_elements:
            mock_ui_elements = [
                {"text": "Default Element", "bounds": [0, 0, 100, 50], "clickable": True}
            ]
        
        return {
            "status": "success",
            "step": self.step_count,
            "action_executed": action,
            "action_type": action_type,
            "element_id": element_id,
            "target": target,
            "coordinates": coordinates,
            "message": f"Mock executed: {action_type} on element {element_id} ({target})",
            "ui_elements": mock_ui_elements,
            "pixels": np.zeros((1080, 1920, 3), dtype=np.uint8)
        }

    def _convert_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Convert high-level action to AndroidWorld action format."""
        action_type = action.get("type", "tap")
        
        if action_type == "tap":
            target = action.get("target", "")
            # Parse coordinates or UI element reference
            if "coordinates" in action:
                coords = action["coordinates"]
                return {
                    "action_type": "tap",
                    "coordinate": coords
                }
            else:
                # Default center tap for demo
                return {
                    "action_type": "tap", 
                    "coordinate": [500, 500]
                }
        
        return {"action_type": "no_op"}

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get current environment state."""
        if self.current_state:
            return {
                "pixels": self.current_state.pixels if hasattr(self.current_state, 'pixels') else None,
                "ui_elements": self.current_state.ui_elements if hasattr(self.current_state, 'ui_elements') else []
            }
        return None
