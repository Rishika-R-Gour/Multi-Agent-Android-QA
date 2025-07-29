try:
    import android_world.registry as reg
    from android_world import suite_utils
    ANDROID_WORLD_AVAILABLE = True
except ImportError:
    # Mock the registry for when Android World is not available
    ANDROID_WORLD_AVAILABLE = False
    reg = None
    suite_utils = None

from typing import Dict, Any, Optional
import logging
import time

class SimpleRunner:
    """A lightweight wrapper to give reset() and step() for tasks without EpisodeRunner."""
    def __init__(self, task):
        self.task = task

    def reset(self):
        # Try different init methods that may exist
        if hasattr(self.task, 'reset'):
            return self.task.reset()
        elif hasattr(self.task, 'start'):
            return self.task.start()
        elif hasattr(self.task, 'initialize'):
            return self.task.initialize()
        else:
            print("Task has no recognizable reset method")
            return None

    def step(self, action):
        # Try different step methods
        if hasattr(self.task, 'step'):
            return self.task.step(action)
        elif hasattr(self.task, 'execute'):
            return self.task.execute(action)
        elif hasattr(self.task, 'run'):
            return self.task.run(action)
        else:
            print("Task has no recognizable step method")
            return None

class EnhancedExecutorAgent:
    """
    Enhanced Executor Agent with better error handling and UI interaction capabilities.
    Falls back to mock mode when Android World is not available.
    """
    
    def __init__(self, task_name: str = "settings_wifi"):
        self.task_name = task_name
        self.logger = logging.getLogger(f"EnhancedExecutorAgent.{task_name}")
        
        if ANDROID_WORLD_AVAILABLE and reg:
            # Try to initialize with real Android World
            try:
                self.task = reg.Umbrella().build_task('settings_wifi', is_safe=True)
                self.runner = SimpleRunner(self.task)
                self.real_mode = True
                self.logger.info("Initialized with real Android World")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Android World: {e}. Using mock mode.")
                self._init_mock_mode()
        else:
            self._init_mock_mode()
    
    def _init_mock_mode(self):
        """Initialize in mock mode for testing without Android World."""
        self.task = None
        self.runner = None
        self.real_mode = False
        self.logger.info("Initialized in mock mode")
    
    def execute_step(self, step: Dict[str, Any], env_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test step with enhanced error handling.
        
        Args:
            step: Step definition with action, target, etc.
            env_state: Current environment state
            
        Returns:
            Execution result with success status and details
        """
        
        if self.real_mode and self.runner:
            return self._execute_real_step(step, env_state)
        else:
            return self._execute_mock_step(step, env_state)
    
    def _execute_real_step(self, step: Dict[str, Any], env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step with real Android World."""
        try:
            action = step.get("action", "unknown")
            target = step.get("target", "unknown")
            
            # Map actions to Android World operations
            if action == "tap":
                result = self._execute_tap_action(target, env_state)
            elif action == "toggle":
                result = self._execute_toggle_action(target, env_state)
            elif action == "navigate":
                result = self._execute_navigate_action(target, env_state)
            elif action == "verify":
                result = self._execute_verify_action(target, env_state)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            return result
            
        except Exception as e:
            self.logger.error(f"Real step execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": step.get("action"),
                "target": step.get("target")
            }
    
    def _execute_mock_step(self, step: Dict[str, Any], env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step in mock mode for testing."""
        
        action = step.get("action", "unknown")
        target = step.get("target", "unknown")
        
        # Simulate realistic execution with occasional failures
        import random
        success_probability = 0.85  # 85% success rate
        
        # Add small delay to simulate real execution
        time.sleep(0.1)
        
        success = random.random() < success_probability
        
        if success:
            return {
                "success": True,
                "action": action,
                "target": target,
                "message": f"Mock execution of {action} on {target} completed successfully",
                "execution_time": 0.1
            }
        else:
            # Simulate different types of failures
            failure_types = [
                "element_not_found",
                "timeout",
                "ui_state_changed",
                "permission_denied"
            ]
            failure_type = random.choice(failure_types)
            
            return {
                "success": False,
                "action": action,
                "target": target,
                "error": f"Mock failure: {failure_type}",
                "failure_type": failure_type,
                "execution_time": 0.1
            }
    
    def _execute_tap_action(self, target: str, env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tap action on target element."""
        # This would contain real Android World tap logic
        return {"success": True, "action": "tap", "target": target}
    
    def _execute_toggle_action(self, target: str, env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute toggle action on target element."""
        # This would contain real Android World toggle logic
        return {"success": True, "action": "toggle", "target": target}
    
    def _execute_navigate_action(self, target: str, env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute navigation action to target."""
        # This would contain real Android World navigation logic
        return {"success": True, "action": "navigate", "target": target}
    
    def _execute_verify_action(self, target: str, env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute verification action."""
        # This would contain real Android World verification logic
        return {"success": True, "action": "verify", "target": target}

class ExecutorAgent:
    def __init__(self, task_name="ContactsAddContact", family="android_world"):
        # Load the task metadata
        reg_instance = reg.TaskRegistry()
        tasks = reg_instance.get_registry(family)
        if task_name not in tasks:
            raise ValueError(f"Task {task_name} not found in {family} tasks!")
        task_info = tasks[task_name]
        task = suite_utils._instantiate_task(task_info)
        self.runner = SimpleRunner(task)

        # Start the environment
        self.obs = self.runner.reset()
        print("[DEBUG] Initial observation keys:", self.obs.keys())
        print("[DEBUG] Full observation content:", self.obs)
 
    def find_element(self, ui_tree, keyword):
        """Find a clickable element by keyword in the UI tree."""
        for el in ui_tree:
            if keyword.lower() in str(el).lower() and el.get("clickable", False):
                return el.get("id")
        return None

    def execute_step(self, step_text):
        """Execute a Planner step by tapping or typing based on the ui_tree."""
        ui_tree = self.obs.get("ui_tree", [])

        element_id = self.find_element(ui_tree, step_text)
        if element_id:
            action = {"action_type": "touch", "element_id": element_id}
            self.obs = self.runner.step(action)
            print(f"[Executor] Tapped '{step_text}' (element ID {element_id})")
        elif "type" in step_text.lower() and ui_tree:
            action = {"action_type": "input_text", "text": step_text, "element_id": ui_tree[0].get("id")}
            self.obs = self.runner.step(action)
            print(f"[Executor] Typed '{step_text}'")
        else:
            print(f"[Executor] Could not find element for: {step_text}")
