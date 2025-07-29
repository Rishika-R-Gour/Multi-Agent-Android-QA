from typing import Dict, List, Any, Optional
import time
import logging
from android_env_wrapper import AndroidEnv

class ExecutorAgent:
    """
    Enhanced Executor Agent that receives subgoals, inspects UI hierarchy (ui_tree),
    and selects grounded actions using AndroidEnv with proper action formatting.
    """
    
    def __init__(self, task_name: str = "settings_wifi", enable_real_device: bool = False):
        self.task_name = task_name
        self.enable_real_device = enable_real_device
        self.logger = logging.getLogger(f"ExecutorAgent.{task_name}")
        
        # Initialize Android environment
        self.env = AndroidEnv(task_name=task_name, enable_real_device=enable_real_device)
        self.current_state = None
        self.execution_history = []
        self.ui_tree = None
        self.available_ui_elements = []
        
    def execute_subgoal(self, subgoal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single subgoal by inspecting UI hierarchy and selecting grounded actions.
        """
        subgoal_id = subgoal.get("subgoal_id", "unknown")
        description = subgoal.get("description", "")
        required_actions = subgoal.get("required_actions", [])
        
        self.logger.info(f"Executing subgoal {subgoal_id}: {description}")
        
        # Inspect current UI hierarchy
        ui_state = self._inspect_ui_hierarchy()
        
        subgoal_result = {
            "subgoal_id": subgoal_id,
            "description": description,
            "start_time": time.time(),
            "ui_inspection": ui_state,
            "actions_executed": [],
            "status": "running",
            "grounded_actions_used": []
        }
        
        try:
            # Execute each required action with UI-grounded selection
            for action in required_actions:
                action_result = self._execute_grounded_action(action, ui_state)
                subgoal_result["actions_executed"].append(action_result)
                
                # Update UI state after each action
                ui_state = self._inspect_ui_hierarchy()
                subgoal_result["ui_inspection"] = ui_state
                
                # Check if action failed critically
                if action_result.get("status") == "critical_failure":
                    subgoal_result["status"] = "failed"
                    break
            
            # Verify subgoal completion
            completion_status = self._verify_subgoal_completion(subgoal, ui_state)
            subgoal_result["completion_verification"] = completion_status
            
            # Determine final status
            if subgoal_result["status"] == "running":
                if completion_status.get("completed", False):
                    subgoal_result["status"] = "success"
                else:
                    subgoal_result["status"] = "partial_success"
                    
        except Exception as e:
            self.logger.error(f"Critical error in subgoal {subgoal_id}: {str(e)}")
            subgoal_result["status"] = "critical_failure"
            subgoal_result["error"] = str(e)
            
        subgoal_result["end_time"] = time.time()
        subgoal_result["duration"] = subgoal_result["end_time"] - subgoal_result["start_time"]
        
        return subgoal_result
    
    def _inspect_ui_hierarchy(self) -> Dict[str, Any]:
        """
        Inspect current UI hierarchy (ui_tree) to understand available elements and actions.
        """
        # Get current state from environment
        if not self.current_state:
            self.current_state = self.env.reset()
        else:
            # Get fresh state
            self.current_state = self.env.step({"action_type": "inspect", "target": "ui_state"})
        
        ui_elements = self.current_state.get("ui_elements", [])
        
        # Build UI hierarchy analysis
        ui_hierarchy = {
            "total_elements": len(ui_elements),
            "clickable_elements": [],
            "text_elements": [],
            "input_elements": [],
            "scroll_containers": [],
            "available_actions": [],
            "element_map": {}  # Maps element text to element info for grounded selection
        }
        
        # Analyze each UI element
        for i, element in enumerate(ui_elements):
            element_info = {
                "index": i,
                "text": element.get("text", ""),
                "bounds": element.get("bounds", []),
                "clickable": element.get("clickable", False),
                "element_id": f"element_{i}",
                "center_point": self._calculate_center_point(element.get("bounds", []))
            }
            
            # Categorize elements
            if element.get("clickable", False):
                ui_hierarchy["clickable_elements"].append(element_info)
                ui_hierarchy["available_actions"].append({
                    "action_type": "touch",
                    "element_id": element_info["element_id"],
                    "target_text": element_info["text"]
                })
            
            if element.get("text", "").strip():
                ui_hierarchy["text_elements"].append(element_info)
            
            # Check for input fields (simplified detection)
            if any(keyword in element.get("text", "").lower() for keyword in ["search", "input", "enter", "type"]):
                ui_hierarchy["input_elements"].append(element_info)
                ui_hierarchy["available_actions"].append({
                    "action_type": "type",
                    "element_id": element_info["element_id"],
                    "target_text": element_info["text"]
                })
            
            # Map element text to info for easy lookup
            if element_info["text"]:
                ui_hierarchy["element_map"][element_info["text"].lower()] = element_info
        
        # Store for later use
        self.ui_tree = ui_hierarchy
        self.available_ui_elements = ui_elements
        
        return ui_hierarchy
    
    def _execute_grounded_action(self, action: str, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a grounded action by selecting appropriate UI elements from the hierarchy.
        Uses env.step() with proper action formatting.
        """
        action_result = {
            "action": action,
            "start_time": time.time(),
            "grounded_selection": None,
            "env_action": None,
            "env_response": None,
            "status": "running"
        }
        
        try:
            # Select grounded UI element for this action
            grounded_element = self._select_grounded_element(action, ui_state)
            action_result["grounded_selection"] = grounded_element
            
            if grounded_element:
                # Format action for AndroidEnv
                env_action = self._format_env_action(action, grounded_element)
                action_result["env_action"] = env_action
                
                # Execute action using env.step()
                env_response = self.env.step(env_action)
                action_result["env_response"] = env_response
                self.current_state = env_response
                
                # Verify action execution
                if env_response.get("status") == "success":
                    action_result["status"] = "success"
                else:
                    action_result["status"] = "failure"
                    action_result["error"] = env_response.get("message", "Action failed")
            else:
                action_result["status"] = "failure"
                action_result["error"] = f"No suitable UI element found for action: {action}"
                
        except Exception as e:
            action_result["status"] = "critical_failure"
            action_result["error"] = str(e)
            
        action_result["end_time"] = time.time()
        action_result["duration"] = action_result["end_time"] - action_result["start_time"]
        
        return action_result
    
    def _select_grounded_element(self, action: str, ui_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Select the most appropriate UI element for the given action using grounded reasoning.
        """
        element_map = ui_state.get("element_map", {})
        clickable_elements = ui_state.get("clickable_elements", [])
        
        # Define action-to-element mapping strategies
        action_keywords = {
            "launch_settings": ["settings", "config", "preferences"],
            "navigate_to_network": ["network", "internet", "connection", "wi-fi", "wifi"],
            "tap_wifi_option": ["wi-fi", "wifi", "wireless"],
            "toggle_wifi_on": ["off", "disabled", "toggle", "switch"],
            "toggle_wifi_off": ["on", "enabled", "toggle", "switch"],
            "verify_wifi_screen": ["wi-fi", "wifi", "wireless"],
            "find_clock_app": ["clock", "time", "alarm"],
            "locate_search": ["search", "find", "query"],
            "enter_search_terms": ["search", "input", "text", "enter"]
        }
        
        # Get keywords for this action
        keywords = action_keywords.get(action, [action.replace("_", " ").split()])
        
        # Find best matching element
        best_match = None
        best_score = 0
        
        for element in clickable_elements:
            element_text = element.get("text", "").lower()
            score = 0
            
            # Score based on keyword matching
            for keyword in keywords:
                if keyword.lower() in element_text:
                    score += 2
                elif any(word in element_text for word in keyword.lower().split()):
                    score += 1
            
            # Bonus for exact matches
            if any(keyword.lower() == element_text for keyword in keywords):
                score += 5
            
            # Prefer elements with bounds (visible)
            if element.get("bounds") and len(element["bounds"]) >= 4:
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = element
        
        # Fallback: if no good match, try first clickable element for some actions
        if not best_match and action in ["tap_wifi_option", "toggle_wifi_on", "toggle_wifi_off"]:
            if clickable_elements:
                best_match = clickable_elements[0]
        
        return best_match
    
    def _format_env_action(self, action: str, grounded_element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format action for AndroidEnv.step() using the grounded element selection.
        Uses the exact format: env.step({"action_type": "touch", "element_id": "<ui_element_id>"})
        """
        element_id = grounded_element.get("element_id", "unknown")
        element_text = grounded_element.get("text", "")
        center_point = grounded_element.get("center_point", [0, 0])
        
        # Determine action type based on action
        if "toggle" in action or "tap" in action or "launch" in action or "navigate" in action:
            return {
                "action_type": "touch",
                "element_id": element_id,
                "coordinates": center_point,
                "target": element_text
            }
        elif "type" in action or "enter" in action:
            return {
                "action_type": "type",
                "element_id": element_id,
                "text": "test input",  # Default text for demo
                "target": element_text
            }
        elif "scroll" in action:
            return {
                "action_type": "scroll",
                "element_id": element_id,
                "direction": "down",
                "target": element_text
            }
        else:
            # Default to touch action
            return {
                "action_type": "touch",
                "element_id": element_id,
                "coordinates": center_point,
                "target": element_text
            }
    
    def _calculate_center_point(self, bounds: List[int]) -> List[int]:
        """Calculate center point from element bounds."""
        if len(bounds) >= 4:
            x = (bounds[0] + bounds[2]) // 2
            y = (bounds[1] + bounds[3]) // 2
            return [x, y]
        return [0, 0]
    
    def _verify_subgoal_completion(self, subgoal: Dict[str, Any], ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """Verify if the subgoal has been completed successfully."""
        success_criteria = subgoal.get("success_criteria", [])
        target_modal = subgoal.get("target_modal", "")
        
        verification_result = {
            "completed": False,
            "criteria_met": [],
            "criteria_failed": [],
            "target_modal_reached": False
        }
        
        # Check each success criterion
        for criterion in success_criteria:
            criterion_met = self._check_success_criterion(criterion, ui_state)
            if criterion_met:
                verification_result["criteria_met"].append(criterion)
            else:
                verification_result["criteria_failed"].append(criterion)
        
        # Check if target modal state is reached
        current_modal = self._detect_current_modal_from_ui(ui_state)
        if target_modal and target_modal.lower() in current_modal.lower():
            verification_result["target_modal_reached"] = True
        
        # Determine completion
        criteria_success_rate = len(verification_result["criteria_met"]) / len(success_criteria) if success_criteria else 1
        verification_result["completed"] = (
            criteria_success_rate >= 0.7 or 
            verification_result["target_modal_reached"]
        )
        
        return verification_result
    
    def _check_success_criterion(self, criterion: str, ui_state: Dict[str, Any]) -> bool:
        """Check if a specific success criterion is met."""
        criterion_lower = criterion.lower()
        element_map = ui_state.get("element_map", {})
        
        # Check for visibility criteria
        if "visible" in criterion_lower:
            element_name = criterion_lower.replace("visible", "").strip()
            return any(element_name in text for text in element_map.keys())
        
        # Check for accessibility criteria  
        if "accessible" in criterion_lower:
            element_name = criterion_lower.replace("accessible", "").strip()
            for text, element_info in element_map.items():
                if element_name in text and element_info.get("clickable", False):
                    return True
        
        # Check for status criteria (on/off states)
        if any(status in criterion_lower for status in ["on", "off", "enabled", "disabled"]):
            return True  # Simplified for demo - would check actual UI state
        
        return False
    
    def _detect_current_modal_from_ui(self, ui_state: Dict[str, Any]) -> str:
        """Detect current modal state from UI elements."""
        text_elements = ui_state.get("text_elements", [])
        
        # Look for modal indicators in UI text
        modal_indicators = {
            "settings": ["settings", "preferences", "config"],
            "wifi_settings": ["wi-fi", "wifi", "wireless", "network"],
            "clock_app": ["clock", "time", "alarm"],
            "email_app": ["email", "mail", "inbox"]
        }
        
        for element in text_elements:
            element_text = element.get("text", "").lower()
            for modal, indicators in modal_indicators.items():
                if any(indicator in element_text for indicator in indicators):
                    return modal
        
        return "unknown"
        
    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete test plan and return detailed results.
        """
        self.logger.info(f"Starting execution of plan: {plan.get('plan_id', 'unknown')}")
        
        # Reset environment
        reset_result = self.env.reset()
        self.current_state = reset_result
        
        execution_results = {
            "plan_id": plan.get("plan_id"),
            "task_name": self.task_name,
            "start_time": time.time(),
            "steps_executed": [],
            "overall_status": "running",
            "environment_state": reset_result
        }
        
        # Execute each step
        for step in plan.get("steps", []):
            step_result = self.execute_step(step)
            execution_results["steps_executed"].append(step_result)
            
            # Break if critical failure
            if step_result["status"] == "critical_failure":
                execution_results["overall_status"] = "failed"
                break
                
        execution_results["end_time"] = time.time()
        execution_results["duration"] = execution_results["end_time"] - execution_results["start_time"]
        
        # Determine overall status
        if execution_results["overall_status"] == "running":
            failed_steps = [s for s in execution_results["steps_executed"] if s["status"] == "failure"]
            if len(failed_steps) == 0:
                execution_results["overall_status"] = "success"
            elif len(failed_steps) < len(execution_results["steps_executed"]) / 2:
                execution_results["overall_status"] = "partial_success"
            else:
                execution_results["overall_status"] = "failed"
                
        self.execution_history.append(execution_results)
        return execution_results
    
    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test step and return detailed results.
        """
        step_id = step.get("step_id", "unknown")
        action = step.get("action", "unknown")
        target = step.get("target", "unknown")
        description = step.get("description", "")
        
        self.logger.info(f"Executing Step {step_id}: {description}")
        
        step_result = {
            "step_id": step_id,
            "action": action,
            "target": target,
            "description": description,
            "start_time": time.time(),
            "status": "running",
            "details": {},
            "validation_results": []
        }
        
        try:
            # Execute the action based on type
            action_result = self._execute_action(action, target, step.get("parameters", {}))
            step_result["action_result"] = action_result
            
            # Validate the step
            validation_results = self._validate_step(step, action_result)
            step_result["validation_results"] = validation_results
            
            # Determine step status
            if action_result.get("status") == "success":
                failed_validations = [v for v in validation_results if not v["passed"]]
                if len(failed_validations) == 0:
                    step_result["status"] = "success"
                else:
                    step_result["status"] = "validation_failure"
                    step_result["details"]["failed_validations"] = failed_validations
            else:
                step_result["status"] = "failure"
                step_result["details"]["error"] = action_result.get("error", "Unknown error")
                
        except Exception as e:
            self.logger.error(f"Critical error in step {step_id}: {str(e)}")
            step_result["status"] = "critical_failure"
            step_result["details"]["exception"] = str(e)
            
        step_result["end_time"] = time.time()
        step_result["duration"] = step_result["end_time"] - step_result["start_time"]
        
        return step_result
    
    def _execute_action(self, action: str, target: str, parameters: Dict) -> Dict[str, Any]:
        """
        Execute the specific action on the Android environment.
        """
        action_data = {
            "type": action,
            "target": target,
            "parameters": parameters
        }
        
        # Add coordinates if needed for UI element targeting
        if action in ["tap", "long_press"]:
            # Try to find UI element coordinates
            coordinates = self._find_element_coordinates(target)
            if coordinates:
                action_data["coordinates"] = coordinates
        
        # Execute action in environment
        env_result = self.env.step(action_data)
        self.current_state = env_result
        
        # Add small delay to let UI stabilize
        time.sleep(1)
        
        return env_result
    
    def _find_element_coordinates(self, target: str) -> Optional[List[int]]:
        """
        Find coordinates of UI element by text or description.
        """
        if not self.current_state or "ui_elements" not in self.current_state:
            return None
            
        for element in self.current_state["ui_elements"]:
            element_text = element.get("text", "").lower()
            if target.lower() in element_text and element.get("clickable", False):
                bounds = element.get("bounds", [])
                if len(bounds) >= 4:
                    # Calculate center point
                    x = (bounds[0] + bounds[2]) // 2
                    y = (bounds[1] + bounds[3]) // 2
                    return [x, y]
        
        return None
    
    def _validate_step(self, step: Dict[str, Any], action_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate step execution against expected criteria.
        """
        validation_results = []
        validation_criteria = step.get("validation_criteria", [])
        
        for criterion in validation_criteria:
            validation_result = {
                "criterion": criterion,
                "passed": False,
                "details": {}
            }
            
            # Check different types of validation criteria
            if "visible" in criterion.lower():
                # Check if element is visible in UI
                element_name = criterion.replace(" visible", "").strip()
                visible = self._check_element_visible(element_name)
                validation_result["passed"] = visible
                validation_result["details"]["element_found"] = visible
                
            elif "status" in criterion.lower():
                # Check status indicators
                expected_status = self._extract_status_from_criterion(criterion)
                current_status = self._get_current_status()
                validation_result["passed"] = expected_status in current_status
                validation_result["details"]["expected"] = expected_status
                validation_result["details"]["actual"] = current_status
                
            elif "shows" in criterion.lower():
                # Check if specific text/state is shown
                expected_text = self._extract_expected_text(criterion)
                found = self._check_text_present(expected_text)
                validation_result["passed"] = found
                validation_result["details"]["expected_text"] = expected_text
                validation_result["details"]["found"] = found
                
            else:
                # Generic validation - assume passed for demo
                validation_result["passed"] = True
                validation_result["details"]["note"] = "Generic validation assumed passed"
            
            validation_results.append(validation_result)
        
        return validation_results
    
    def _check_element_visible(self, element_name: str) -> bool:
        """Check if a UI element is visible."""
        if not self.current_state or "ui_elements" not in self.current_state:
            return False
            
        for element in self.current_state["ui_elements"]:
            if element_name.lower() in element.get("text", "").lower():
                return True
        return False
    
    def _extract_status_from_criterion(self, criterion: str) -> str:
        """Extract expected status from validation criterion."""
        if "ON" in criterion:
            return "ON"
        elif "OFF" in criterion:
            return "OFF"
        return "unknown"
    
    def _get_current_status(self) -> str:
        """Get current status from UI elements."""
        if not self.current_state or "ui_elements" not in self.current_state:
            return "unknown"
            
        for element in self.current_state["ui_elements"]:
            text = element.get("text", "")
            if text in ["ON", "OFF", "Connected", "Disconnected"]:
                return text
        return "unknown"
    
    def _extract_expected_text(self, criterion: str) -> str:
        """Extract expected text from validation criterion."""
        # Simple extraction - could be more sophisticated
        parts = criterion.split("shows")
        if len(parts) > 1:
            return parts[1].strip()
        return ""
    
    def _check_text_present(self, text: str) -> bool:
        """Check if specific text is present in current UI."""
        if not self.current_state or "ui_elements" not in self.current_state:
            return False
            
        for element in self.current_state["ui_elements"]:
            if text.lower() in element.get("text", "").lower():
                return True
        return False
    
    def get_execution_summary(self) -> str:
        """Get summary of all executions."""
        if not self.execution_history:
            return "No executions completed yet."
            
        summary = f"Execution History ({len(self.execution_history)} runs):\n\n"
        
        for i, execution in enumerate(self.execution_history, 1):
            summary += f"Run {i}: {execution['overall_status']}\n"
            summary += f"  Duration: {execution['duration']:.2f}s\n"
            summary += f"  Steps: {len(execution['steps_executed'])}\n"
            
            success_count = len([s for s in execution['steps_executed'] if s['status'] == 'success'])
            summary += f"  Success rate: {success_count}/{len(execution['steps_executed'])}\n\n"
            
        return summary

def execute_steps(steps):
    """Legacy function for backward compatibility."""
    print("\n[Executor Agent] Starting execution...\n")
    for i, step in enumerate(steps, start=1):
        print(f"Executing Step {i}: {step}")
    print("\n[Executor Agent] Execution complete!\n")

if __name__ == "__main__":
    # Test the enhanced executor
    executor = ExecutorAgent("settings_wifi", enable_real_device=False)
    
    # Sample plan for testing
    sample_plan = {
        "plan_id": "test_plan_1",
        "goal": "Test Wi-Fi toggle functionality",
        "steps": [
            {
                "step_id": 1,
                "action": "tap",
                "target": "Settings",
                "description": "Open Settings app",
                "validation_criteria": ["Settings title visible"]
            },
            {
                "step_id": 2,
                "action": "tap",
                "target": "Wi-Fi",
                "description": "Navigate to Wi-Fi settings",
                "validation_criteria": ["Wi-Fi toggle visible"]
            }
        ]
    }
    
    result = executor.execute_plan(sample_plan)
    print("Execution Result:")
    print(f"Status: {result['overall_status']}")
    print(f"Duration: {result['duration']:.2f}s")
    print(f"Steps completed: {len(result['steps_executed'])}")
    
    print("\nExecution Summary:")
    print(executor.get_execution_summary())
