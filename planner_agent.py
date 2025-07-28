from typing import Dict, List, Any, Optional
import json
import logging
import time
from datetime import datetime
from android_env_wrapper import AndroidEnv

class Message:
    """Agent-S style message structure for communication."""
    def __init__(self, role: str, content: str, metadata: Optional[Dict] = None):
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = None

class PlannerAgent:
    """
    Enhanced Planner Agent with dynamic reasoning about modal states and adaptive planning.
    Generates actionable, app-specific subgoals that update based on current environment state.
    """
    
    def __init__(self, task_name: str = "settings_wifi"):
        self.task_name = task_name
        self.logger = logging.getLogger(f"PlannerAgent.{task_name}")
        self.conversation_history = []
        self.current_plan = None
        self.execution_context = {}
        self.modal_state_tracker = {}
        
        # Initialize Android environment for context
        self.env = AndroidEnv(task_name=task_name, enable_real_device=False)
        
        # Dynamic planning state
        self.current_app_state = "unknown"
        self.navigation_stack = []
        self.available_actions = []
        self.plan_adaptation_history = []
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to conversation history."""
        message = Message(role, content, metadata)
        self.conversation_history.append(message)
        
    def generate_test_plan(self, goal: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a dynamic test plan with modal state reasoning and app-specific subgoals.
        Updates plan based on current environment state and execution context.
        """
        self.add_message("user", f"Generate adaptive QA test plan for: {goal}")
        
        # Get initial environment state for context
        env_state = self.env.reset()
        self._update_modal_state_tracker(env_state)
        
        # Analyze the goal and break it into actionable subgoals
        subgoals = self._decompose_goal_into_subgoals(goal, env_state)
        
        # Create adaptive plan with modal state reasoning
        plan = self._create_adaptive_plan(goal, subgoals, env_state, context)
        
        # Add dynamic adaptation capabilities
        plan["adaptation_config"] = {
            "modal_state_tracking": True,
            "dynamic_replanning": True,
            "context_awareness": True,
            "fallback_strategies": self._generate_fallback_strategies(goal)
        }
        
        self.current_plan = plan
        self.add_message("assistant", f"Generated adaptive plan with {len(plan['steps'])} steps", 
                        {"plan_id": plan["plan_id"], "subgoals": len(subgoals)})
        
        return plan
    
    def _decompose_goal_into_subgoals(self, goal: str, env_state: Dict) -> List[Dict[str, Any]]:
        """
        Decompose high-level goal into actionable, app-specific subgoals.
        Uses modal state reasoning to understand app flow requirements.
        """
        goal_lower = goal.lower()
        subgoals = []
        
        if "wi-fi" in goal_lower or "wifi" in goal_lower:
            subgoals = self._decompose_wifi_goal(goal, env_state)
        elif "alarm" in goal_lower or "clock" in goal_lower:
            subgoals = self._decompose_alarm_goal(goal, env_state)
        elif "email" in goal_lower:
            subgoals = self._decompose_email_goal(goal, env_state)
        else:
            subgoals = self._decompose_generic_goal(goal, env_state)
        
        # Add modal state reasoning to each subgoal
        for subgoal in subgoals:
            subgoal["modal_requirements"] = self._analyze_modal_requirements(subgoal)
            subgoal["app_specific_context"] = self._get_app_specific_context(subgoal)
            subgoal["adaptation_triggers"] = self._identify_adaptation_triggers(subgoal)
        
        return subgoals
    
    def _decompose_wifi_goal(self, goal: str, env_state: Dict) -> List[Dict[str, Any]]:
        """Decompose WiFi testing goal into app-specific subgoals with modal state awareness."""
        return [
            {
                "subgoal_id": "wifi_001",
                "description": "Navigate to WiFi settings",
                "modal_context": "home_screen",
                "target_modal": "settings_app",
                "required_actions": ["launch_settings", "navigate_to_network"],
                "success_criteria": ["settings_app_visible", "network_section_accessible"],
                "state_dependencies": ["device_unlocked", "home_screen_available"]
            },
            {
                "subgoal_id": "wifi_002", 
                "description": "Access WiFi configuration",
                "modal_context": "settings_network",
                "target_modal": "wifi_settings",
                "required_actions": ["tap_wifi_option", "verify_wifi_screen"],
                "success_criteria": ["wifi_toggle_visible", "wifi_list_available"],
                "state_dependencies": ["network_settings_loaded", "wifi_option_clickable"]
            },
            {
                "subgoal_id": "wifi_003",
                "description": "Test WiFi toggle functionality",
                "modal_context": "wifi_settings",
                "target_modal": "wifi_settings_active",
                "required_actions": ["toggle_wifi_on", "verify_activation", "toggle_wifi_off", "verify_deactivation"],
                "success_criteria": ["wifi_status_changes", "network_list_updates", "connectivity_reflects_state"],
                "state_dependencies": ["wifi_settings_accessible", "toggle_responsive"]
            },
            {
                "subgoal_id": "wifi_004",
                "description": "Verify state persistence",
                "modal_context": "wifi_settings",
                "target_modal": "verified_state",
                "required_actions": ["exit_settings", "re_enter_settings", "verify_state_maintained"],
                "success_criteria": ["state_persisted", "ui_consistent"],
                "state_dependencies": ["navigation_functional", "state_storage_working"]
            }
        ]
    
    def _decompose_alarm_goal(self, goal: str, env_state: Dict) -> List[Dict[str, Any]]:
        """Decompose alarm testing goal into app-specific subgoals."""
        return [
            {
                "subgoal_id": "alarm_001",
                "description": "Launch clock application",
                "modal_context": "home_screen",
                "target_modal": "clock_app",
                "required_actions": ["find_clock_app", "launch_app"],
                "success_criteria": ["clock_app_loaded", "main_interface_visible"],
                "state_dependencies": ["clock_app_installed", "app_permissions_granted"]
            },
            {
                "subgoal_id": "alarm_002",
                "description": "Navigate to alarm section",
                "modal_context": "clock_app",
                "target_modal": "alarm_management",
                "required_actions": ["locate_alarm_tab", "switch_to_alarms"],
                "success_criteria": ["alarm_list_visible", "add_alarm_accessible"],
                "state_dependencies": ["clock_app_responsive", "alarm_feature_available"]
            },
            {
                "subgoal_id": "alarm_003",
                "description": "Create and configure alarm",
                "modal_context": "alarm_management",
                "target_modal": "alarm_creation",
                "required_actions": ["tap_add_alarm", "set_time", "configure_options", "save_alarm"],
                "success_criteria": ["alarm_created", "time_set_correctly", "alarm_in_list"],
                "state_dependencies": ["alarm_creation_functional", "time_picker_responsive"]
            },
            {
                "subgoal_id": "alarm_004",
                "description": "Test alarm activation/deactivation",
                "modal_context": "alarm_management",
                "target_modal": "alarm_configured",
                "required_actions": ["toggle_alarm_on", "verify_active", "toggle_alarm_off", "verify_inactive"],
                "success_criteria": ["alarm_state_changes", "ui_reflects_status"],
                "state_dependencies": ["alarm_toggle_functional", "state_tracking_working"]
            }
        ]
    
    def _decompose_email_goal(self, goal: str, env_state: Dict) -> List[Dict[str, Any]]:
        """Decompose email testing goal into app-specific subgoals."""
        return [
            {
                "subgoal_id": "email_001",
                "description": "Access email application",
                "modal_context": "home_screen",
                "target_modal": "email_app",
                "required_actions": ["locate_email_app", "launch_email"],
                "success_criteria": ["email_app_loaded", "inbox_visible"],
                "state_dependencies": ["email_app_configured", "network_available"]
            },
            {
                "subgoal_id": "email_002",
                "description": "Access search functionality",
                "modal_context": "email_app",
                "target_modal": "search_interface",
                "required_actions": ["locate_search", "activate_search"],
                "success_criteria": ["search_box_visible", "keyboard_accessible"],
                "state_dependencies": ["email_loaded", "search_feature_available"]
            },
            {
                "subgoal_id": "email_003",
                "description": "Execute search query",
                "modal_context": "search_interface",
                "target_modal": "search_results",
                "required_actions": ["enter_search_terms", "execute_search", "review_results"],
                "success_criteria": ["search_executed", "results_displayed", "results_relevant"],
                "state_dependencies": ["search_functional", "email_index_available"]
            }
        ]
    
    def _decompose_generic_goal(self, goal: str, env_state: Dict) -> List[Dict[str, Any]]:
        """Decompose generic goal into basic subgoals."""
        return [
            {
                "subgoal_id": "generic_001",
                "description": "Identify target application",
                "modal_context": "any",
                "target_modal": "app_identified",
                "required_actions": ["analyze_goal", "identify_target_app"],
                "success_criteria": ["target_app_known"],
                "state_dependencies": ["goal_clear"]
            },
            {
                "subgoal_id": "generic_002",
                "description": "Access target functionality",
                "modal_context": "app_identified",
                "target_modal": "functionality_accessed",
                "required_actions": ["launch_app", "navigate_to_feature"],
                "success_criteria": ["feature_accessible"],
                "state_dependencies": ["app_available", "feature_exists"]
            }
        ]
    
    def _analyze_modal_requirements(self, subgoal: Dict) -> Dict[str, Any]:
        """Analyze what modal states are required for this subgoal."""
        return {
            "entry_conditions": subgoal.get("state_dependencies", []),
            "required_ui_state": subgoal.get("modal_context"),
            "target_ui_state": subgoal.get("target_modal"),
            "modal_transitions": self._identify_modal_transitions(subgoal),
            "blocking_modals": self._identify_blocking_modals(subgoal)
        }
    
    def _identify_modal_transitions(self, subgoal: Dict) -> List[str]:
        """Identify modal state transitions needed."""
        current = subgoal.get("modal_context", "unknown")
        target = subgoal.get("target_modal", "unknown")
        
        # Define common modal transition patterns
        transitions = []
        if current == "home_screen" and "settings" in target:
            transitions = ["home_to_apps", "apps_to_settings"]
        elif current == "settings_network" and "wifi" in target:
            transitions = ["network_to_wifi"]
        elif "app" in current and "feature" in target:
            transitions = ["app_navigation", "feature_access"]
        
        return transitions
    
    def _identify_blocking_modals(self, subgoal: Dict) -> List[str]:
        """Identify modal states that could block this subgoal."""
        blocking_modals = [
            "permission_dialog",
            "error_popup", 
            "loading_screen",
            "network_error",
            "app_crash_dialog",
            "system_notification"
        ]
        
        # Add context-specific blocking modals
        if "wifi" in subgoal.get("description", "").lower():
            blocking_modals.extend(["airplane_mode_active", "wifi_disabled_popup"])
        elif "alarm" in subgoal.get("description", "").lower():
            blocking_modals.extend(["do_not_disturb_warning", "clock_permission_dialog"])
        
        return blocking_modals
    
    def _create_adaptive_plan(self, goal: str, subgoals: List[Dict], env_state: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Create an adaptive plan that can update dynamically based on modal states."""
        
        # Convert subgoals to executable steps with modal state awareness
        steps = []
        for i, subgoal in enumerate(subgoals, 1):
            steps.extend(self._convert_subgoal_to_steps(subgoal, i))
        
        plan = {
            "plan_id": f"adaptive_plan_{self.task_name}_{len(self.conversation_history)}",
            "goal": goal,
            "task_name": self.task_name,
            "subgoals": subgoals,
            "steps": steps,
            "environment_context": env_state,
            "estimated_duration": len(steps) * 25,  # More realistic timing for adaptive execution
            "metadata": {
                "planner_version": "2.0_adaptive",
                "agent_type": "Agent-S_Adaptive_QA_Planner",
                "context": context,
                "modal_state_aware": True,
                "dynamic_replanning": True
            },
            "execution_strategy": {
                "adaptive_execution": True,
                "state_monitoring": True,
                "error_recovery": True,
                "plan_refinement": True
            }
        }
        
        return plan
    
    def _convert_subgoal_to_steps(self, subgoal: Dict, subgoal_index: int) -> List[Dict[str, Any]]:
        """Convert a subgoal into executable steps with modal state checks."""
        steps = []
        base_step_id = subgoal_index * 10
        
        # Pre-step: Modal state verification
        steps.append({
            "step_id": base_step_id - 1,
            "subgoal_id": subgoal["subgoal_id"],
            "action": "verify_modal_state",
            "target": subgoal["modal_context"],
            "description": f"Verify modal state for: {subgoal['description']}",
            "expected_result": f"System in {subgoal['modal_context']} state",
            "validation_criteria": [
                f"Current modal state is {subgoal['modal_context']}",
                "No blocking modals present",
                "Required UI elements accessible"
            ],
            "modal_state_check": True,
            "adaptation_point": True,
            "fallback_actions": ["dismiss_blocking_modals", "navigate_to_required_state"]
        })
        
        # Main execution steps for each required action
        for i, action in enumerate(subgoal["required_actions"], 1):
            steps.append({
                "step_id": base_step_id + i,
                "subgoal_id": subgoal["subgoal_id"],
                "action": self._map_action_to_execution_type(action),
                "target": self._extract_target_from_action(action),
                "description": f"Execute: {action}",
                "expected_result": self._generate_expected_result(action, subgoal),
                "validation_criteria": self._generate_validation_criteria(action, subgoal),
                "modal_state_transition": self._determine_modal_transition(action, subgoal),
                "adaptation_point": True,
                "retry_strategy": self._generate_retry_strategy(action),
                "fallback_actions": self._generate_fallback_actions(action, subgoal)
            })
        
        # Post-step: Success verification
        steps.append({
            "step_id": base_step_id + len(subgoal["required_actions"]) + 1,
            "subgoal_id": subgoal["subgoal_id"],
            "action": "verify_subgoal_completion",
            "target": subgoal["target_modal"],
            "description": f"Verify completion of: {subgoal['description']}",
            "expected_result": f"Subgoal achieved, system in {subgoal['target_modal']} state",
            "validation_criteria": subgoal["success_criteria"],
            "modal_state_check": True,
            "completion_verification": True
        })
        
        return steps
    
    def _map_action_to_execution_type(self, action: str) -> str:
        """Map high-level action to execution type."""
        action_mappings = {
            "launch_settings": "navigate",
            "navigate_to_network": "tap",
            "tap_wifi_option": "tap",
            "toggle_wifi_on": "toggle",
            "toggle_wifi_off": "toggle",
            "verify_activation": "verify",
            "find_clock_app": "search",
            "launch_app": "navigate",
            "locate_search": "locate",
            "enter_search_terms": "type",
            "execute_search": "tap"
        }
        return action_mappings.get(action, "interact")
    
    def _extract_target_from_action(self, action: str) -> str:
        """Extract the target UI element from action description."""
        target_mappings = {
            "launch_settings": "Settings app",
            "navigate_to_network": "Network & internet",
            "tap_wifi_option": "Wi-Fi",
            "toggle_wifi_on": "Wi-Fi toggle",
            "toggle_wifi_off": "Wi-Fi toggle",
            "find_clock_app": "Clock app",
            "locate_search": "Search button",
            "enter_search_terms": "Search box"
        }
        return target_mappings.get(action, action.replace("_", " "))
    
    def _generate_expected_result(self, action: str, subgoal: Dict) -> str:
        """Generate expected result for an action."""
        if "launch" in action:
            return "Application launches successfully"
        elif "navigate" in action or "tap" in action:
            return "Navigation successful, target screen visible"
        elif "toggle" in action:
            return "Toggle state changes as expected"
        elif "verify" in action:
            return "Verification passes, state confirmed"
        else:
            return f"Action '{action}' completes successfully"
    
    def _generate_validation_criteria(self, action: str, subgoal: Dict) -> List[str]:
        """Generate validation criteria for an action."""
        base_criteria = ["Action executes without error", "UI responds appropriately"]
        
        if "wifi" in action.lower():
            base_criteria.extend(["Wi-Fi interface accessible", "Network status updates"])
        elif "settings" in action.lower():
            base_criteria.extend(["Settings menu visible", "Options are clickable"])
        elif "alarm" in action.lower():
            base_criteria.extend(["Alarm interface functional", "Time controls responsive"])
        
        return base_criteria
    
    def _determine_modal_transition(self, action: str, subgoal: Dict) -> Optional[str]:
        """Determine what modal state transition this action should cause."""
        if "launch" in action:
            return f"transition_to_{subgoal.get('target_modal', 'unknown')}"
        elif "navigate" in action:
            return f"navigate_within_{subgoal.get('modal_context', 'app')}"
        return None
    
    def _generate_retry_strategy(self, action: str) -> Dict[str, Any]:
        """Generate retry strategy for an action."""
        return {
            "max_retries": 3,
            "retry_delay": 1.0,
            "retry_conditions": ["element_not_found", "action_failed", "unexpected_modal"],
            "retry_modifications": ["increase_wait_time", "retry_element_location", "dismiss_popup"]
        }
    
    def _generate_fallback_actions(self, action: str, subgoal: Dict) -> List[str]:
        """Generate fallback actions if primary action fails."""
        fallbacks = ["wait_for_ui_stabilization", "refresh_screen"]
        
        if "launch" in action:
            fallbacks.extend(["try_alternative_launch_method", "check_app_availability"])
        elif "tap" in action:
            fallbacks.extend(["try_different_coordinates", "use_accessibility_tap"])
        elif "toggle" in action:
            fallbacks.extend(["long_press_toggle", "use_menu_option"])
        
        return fallbacks
    
    def handle_replanning_request(self, verification_result: Dict[str, Any], 
                                 current_plan: Dict[str, Any], 
                                 current_subgoal_index: int,
                                 ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle dynamic replanning when Verifier signals problems.
        
        Args:
            verification_result: Result from VerifierAgent with detected issues
            current_plan: Current test plan being executed
            current_subgoal_index: Index of subgoal that failed verification
            ui_state: Current UI state for context
            
        Returns:
            Updated plan with replanning modifications
        """
        self.logger.info(f"Handling replanning request for subgoal {current_subgoal_index}")
        
        replanning_result = {
            "replanning_id": f"replan_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "original_plan": current_plan,
            "verification_issues": verification_result,
            "current_subgoal_index": current_subgoal_index,
            "ui_state": ui_state,
            "adaptations_made": [],
            "new_subgoals": [],
            "modified_subgoals": [],
            "status": "processing"
        }
        
        try:
            # Analyze verification issues
            functional_bugs = verification_result.get("functional_bugs", [])
            replanning_suggestions = verification_result.get("replanning_suggestions", [])
            heuristic_issues = verification_result.get("heuristic_checks", {})
            
            # Apply specific replanning strategies
            replanning_result = self._apply_replanning_strategies(
                replanning_result, functional_bugs, replanning_suggestions, ui_state
            )
            
            # Handle modal blocking issues
            if heuristic_issues.get("modal_blocking_detection", {}).get("blocking_detected"):
                replanning_result = self._handle_modal_blocking(replanning_result, ui_state)
            
            # Update the plan with adaptations
            updated_plan = self._generate_updated_plan(
                current_plan, replanning_result, current_subgoal_index
            )
            
            replanning_result["updated_plan"] = updated_plan
            replanning_result["status"] = "completed"
            
            # Log the replanning action
            self._log_replanning_action(replanning_result)
            
        except Exception as e:
            self.logger.error(f"Replanning failed: {e}")
            replanning_result["status"] = "failed"
            replanning_result["error"] = str(e)
            # Return original plan as fallback
            replanning_result["updated_plan"] = current_plan
        
        return replanning_result
    
    def _apply_replanning_strategies(self, replanning_result: Dict, 
                                   functional_bugs: List[Dict], 
                                   suggestions: List[str],
                                   ui_state: Dict) -> Dict:
        """Apply specific replanning strategies based on detected issues."""
        
        for bug in functional_bugs:
            bug_type = bug.get("bug_type", "")
            suggested_action = bug.get("suggested_action", "")
            
            if suggested_action == "dismiss_dialog_and_retry":
                # Add dialog dismissal step
                dismiss_subgoal = {
                    "subgoal_id": f"dismiss_dialog_{len(replanning_result['new_subgoals'])}",
                    "description": "Dismiss error dialog",
                    "modal_context": "error_dialog",
                    "target_modal": "dialog_dismissed",
                    "required_actions": ["tap_dismiss", "tap_ok", "tap_cancel"],
                    "success_criteria": ["dialog_closed", "normal_ui_visible"],
                    "state_dependencies": ["dialog_present"],
                    "replanning_reason": f"Handle {bug_type}: {bug.get('description', '')}"
                }
                replanning_result["new_subgoals"].append(dismiss_subgoal)
                replanning_result["adaptations_made"].append("added_dialog_dismissal")
                
            elif suggested_action == "navigate_to_correct_screen":
                # Add navigation correction steps
                nav_subgoal = {
                    "subgoal_id": f"navigate_correction_{len(replanning_result['new_subgoals'])}",
                    "description": "Navigate to correct screen",
                    "modal_context": "incorrect_screen",
                    "target_modal": "correct_screen",
                    "required_actions": ["identify_current_location", "navigate_back", "navigate_to_target"],
                    "success_criteria": ["correct_screen_visible", "expected_elements_present"],
                    "state_dependencies": ["navigation_available"],
                    "replanning_reason": f"Navigation correction for {bug.get('description', '')}"
                }
                replanning_result["new_subgoals"].append(nav_subgoal)
                replanning_result["adaptations_made"].append("added_navigation_correction")
                
            elif suggested_action == "retry_toggle_action":
                # Modify current subgoal to retry toggle
                retry_subgoal = {
                    "subgoal_id": f"retry_toggle_{len(replanning_result['modified_subgoals'])}",
                    "description": "Retry toggle action with verification",
                    "modal_context": "toggle_interface", 
                    "target_modal": "toggle_completed",
                    "required_actions": ["verify_current_state", "perform_toggle", "verify_new_state"],
                    "success_criteria": ["toggle_state_correct", "ui_reflects_change"],
                    "state_dependencies": ["toggle_accessible"],
                    "replanning_reason": f"Retry toggle due to state mismatch"
                }
                replanning_result["modified_subgoals"].append(retry_subgoal)
                replanning_result["adaptations_made"].append("modified_toggle_retry")
        
        # Handle suggestion-based adaptations
        for suggestion in suggestions:
            if "dismiss error dialog" in suggestion.lower():
                replanning_result["adaptations_made"].append("suggestion_dialog_handling")
            elif "navigation" in suggestion.lower():
                replanning_result["adaptations_made"].append("suggestion_navigation_fix")
            elif "blocking modal" in suggestion.lower():
                replanning_result["adaptations_made"].append("suggestion_modal_handling")
        
        return replanning_result
    
    def _handle_modal_blocking(self, replanning_result: Dict, ui_state: Dict) -> Dict:
        """Handle blocking modal situations."""
        ui_elements = ui_state.get("ui_elements", [])
        
        # Identify type of blocking modal
        modal_type = self._identify_blocking_modal_type(ui_elements)
        
        if modal_type == "permission_dialog":
            permission_subgoal = {
                "subgoal_id": f"handle_permission_{len(replanning_result['new_subgoals'])}",
                "description": "Handle permission dialog",
                "modal_context": "permission_dialog",
                "target_modal": "permission_granted",
                "required_actions": ["read_permission_text", "tap_allow", "verify_permission_granted"],
                "success_criteria": ["permission_dialog_dismissed", "permission_granted"],
                "state_dependencies": ["permission_dialog_present"],
                "replanning_reason": "Handle blocking permission dialog"
            }
            replanning_result["new_subgoals"].append(permission_subgoal)
            
        elif modal_type == "error_popup":
            error_subgoal = {
                "subgoal_id": f"handle_error_{len(replanning_result['new_subgoals'])}",
                "description": "Handle error popup",
                "modal_context": "error_popup",
                "target_modal": "error_dismissed",
                "required_actions": ["read_error_message", "tap_ok", "verify_error_dismissed"],
                "success_criteria": ["error_popup_dismissed", "normal_ui_restored"],
                "state_dependencies": ["error_popup_present"],
                "replanning_reason": "Handle blocking error popup"
            }
            replanning_result["new_subgoals"].append(error_subgoal)
        
        replanning_result["adaptations_made"].append(f"handled_blocking_modal_{modal_type}")
        return replanning_result
    
    def _identify_blocking_modal_type(self, ui_elements: List) -> str:
        """Identify the type of blocking modal present."""
        for element in ui_elements:
            text = element.get("text", "").lower()
            if any(keyword in text for keyword in ["allow", "deny", "permission"]):
                return "permission_dialog"
            elif any(keyword in text for keyword in ["error", "failed", "cannot"]):
                return "error_popup"
            elif any(keyword in text for keyword in ["loading", "please wait"]):
                return "loading_screen"
        
        return "unknown_modal"
    
    def _generate_updated_plan(self, original_plan: Dict, 
                             replanning_result: Dict, 
                             current_index: int) -> Dict:
        """Generate updated plan with replanning adaptations."""
        updated_plan = original_plan.copy()
        original_subgoals = updated_plan.get("subgoals", [])
        
        # Insert new subgoals before the current failing subgoal
        new_subgoals = replanning_result.get("new_subgoals", [])
        insertion_point = current_index
        
        # Insert new subgoals
        for i, new_subgoal in enumerate(new_subgoals):
            original_subgoals.insert(insertion_point + i, new_subgoal)
        
        # Replace modified subgoals
        modified_subgoals = replanning_result.get("modified_subgoals", [])
        for modified_subgoal in modified_subgoals:
            # Replace the current failing subgoal
            if current_index + len(new_subgoals) < len(original_subgoals):
                original_subgoals[current_index + len(new_subgoals)] = modified_subgoal
        
        # Update plan metadata
        updated_plan.update({
            "subgoals": original_subgoals,
            "replanning_applied": True,
            "replanning_timestamp": replanning_result["timestamp"],
            "adaptations_made": replanning_result["adaptations_made"],
            "original_subgoal_count": len(original_plan.get("subgoals", [])),
            "updated_subgoal_count": len(original_subgoals)
        })
        
        return updated_plan
    
    def _log_replanning_action(self, replanning_result: Dict):
        """Log replanning action in structured format."""
        log_entry = {
            "agent": "PlannerAgent",
            "action": "dynamic_replanning",
            "timestamp": replanning_result["timestamp"],
            "replanning_id": replanning_result["replanning_id"],
            "trigger_issues": len(replanning_result["verification_issues"].get("functional_bugs", [])),
            "adaptations_made": replanning_result["adaptations_made"],
            "new_subgoals_added": len(replanning_result["new_subgoals"]),
            "subgoals_modified": len(replanning_result["modified_subgoals"]),
            "status": replanning_result["status"]
        }
        
        # Save to JSON log
        self._save_agent_log(log_entry)
        
        self.logger.info(f"Replanning completed: {log_entry}")

    def _save_agent_log(self, log_entry: Dict):
        """Save agent decision log in JSON format."""
        log_filename = f"qa_planner_log_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Ensure reports directory exists
        import os
        os.makedirs("reports", exist_ok=True)
        
        try:
            with open(f"reports/{log_filename}", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write planner log: {e}")

    def update_plan_dynamically(self, current_plan: Dict[str, Any], 
                              execution_context: Dict[str, Any],
                              verification_feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update the current plan dynamically based on execution feedback and modal state changes.
        This implements the core dynamic replanning capability.
        """
        if not self.current_plan:
            raise ValueError("No current plan to update")
        
        self.logger.info("Updating plan dynamically based on current state and feedback")
        
        # Extract current state from execution context
        current_state = execution_context.get("current_state", {})
        execution_feedback = execution_context.get("execution_feedback", {})
        
        # Update modal state tracker
        self._update_modal_state_tracker(current_state)
        
        # Handle verification feedback if provided
        if verification_feedback and verification_feedback.get("replanning_required"):
            return self.handle_replanning_request(
                verification_feedback, 
                self.current_plan, 
                execution_context.get("current_subgoal_index", 0),
                current_state
            )
        
        # Analyze execution feedback for adaptation needs
        adaptation_needed = self._analyze_adaptation_needs(execution_feedback)
        
        if adaptation_needed:
            # Create updated plan
            updated_plan = self._adapt_plan(current_state, execution_feedback, adaptation_needed)
            
            # Track adaptation history
            self.plan_adaptation_history.append({
                "timestamp": time.time(),
                "trigger": adaptation_needed,
                "original_plan_id": self.current_plan["plan_id"],
                "updated_plan_id": updated_plan["plan_id"],
                "state_context": current_state
            })
            
            self.current_plan = updated_plan
            self.add_message("system", f"Plan adapted: {adaptation_needed['reason']}", 
                           {"adaptation_type": adaptation_needed["type"]})
            
            return updated_plan
        
        return self.current_plan
    
    def _update_modal_state_tracker(self, current_state: Dict[str, Any]):
        """Update the modal state tracker with current environment state."""
        if "ui_elements" in current_state:
            self.modal_state_tracker.update({
                "last_update": time.time(),
                "ui_elements": current_state["ui_elements"],
                "detected_modal": self._detect_current_modal(current_state["ui_elements"]),
                "blocking_elements": self._detect_blocking_elements(current_state["ui_elements"]),
                "available_actions": self._extract_available_actions(current_state["ui_elements"])
            })
    
    def _detect_current_modal(self, ui_elements: List[Dict]) -> str:
        """Detect the current modal state from UI elements."""
        modal_indicators = {
            "settings": ["Settings", "Preferences", "Configuration"],
            "wifi_settings": ["Wi-Fi", "Network", "Internet"],
            "clock_app": ["Clock", "Timer", "Alarm"],
            "email_app": ["Inbox", "Mail", "Messages"],
            "home_screen": ["Home", "Desktop", "Launcher"]
        }
        
        for element in ui_elements:
            element_text = element.get("text", "").lower()
            for modal, indicators in modal_indicators.items():
                if any(indicator.lower() in element_text for indicator in indicators):
                    return modal
        
        return "unknown"
    
    def _detect_blocking_elements(self, ui_elements: List[Dict]) -> List[str]:
        """Detect UI elements that might block execution."""
        blocking_elements = []
        blocking_keywords = ["error", "permission", "loading", "wait", "dialog", "popup"]
        
        for element in ui_elements:
            element_text = element.get("text", "").lower()
            if any(keyword in element_text for keyword in blocking_keywords):
                blocking_elements.append(element_text)
        
        return blocking_elements
    
    def _extract_available_actions(self, ui_elements: List[Dict]) -> List[str]:
        """Extract available actions from current UI state."""
        available_actions = []
        
        for element in ui_elements:
            if element.get("clickable", False):
                available_actions.append(f"tap_{element.get('text', 'unknown').replace(' ', '_').lower()}")
        
        return available_actions
    
    def _analyze_adaptation_needs(self, execution_feedback: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze if plan adaptation is needed based on execution feedback."""
        
        # Check for failed steps that require plan modification
        if execution_feedback.get("status") == "failure":
            failure_reason = execution_feedback.get("error", "unknown")
            
            if "element_not_found" in failure_reason:
                return {
                    "type": "ui_change_adaptation",
                    "reason": "Target UI element not found, need alternative approach",
                    "suggested_action": "update_element_selectors"
                }
            elif "modal_state_mismatch" in failure_reason:
                return {
                    "type": "modal_state_adaptation", 
                    "reason": "Unexpected modal state, need navigation correction",
                    "suggested_action": "correct_navigation_path"
                }
            elif "timeout" in failure_reason:
                return {
                    "type": "timing_adaptation",
                    "reason": "Operation timed out, need longer waits or different approach",
                    "suggested_action": "increase_timeouts"
                }
        
        # Check for blocking modals
        if self.modal_state_tracker.get("blocking_elements"):
            return {
                "type": "blocking_modal_adaptation",
                "reason": "Blocking modal detected, need dismissal strategy",
                "suggested_action": "dismiss_blocking_modals"
            }
        
        return None
    
    def _adapt_plan(self, current_state: Dict, feedback: Dict, adaptation_needed: Dict) -> Dict[str, Any]:
        """Create an adapted version of the current plan."""
        adapted_plan = self.current_plan.copy()
        adapted_plan["plan_id"] = f"{adapted_plan['plan_id']}_adapted_{int(time.time())}"
        
        adaptation_type = adaptation_needed["type"]
        
        if adaptation_type == "ui_change_adaptation":
            adapted_plan["steps"] = self._adapt_steps_for_ui_changes(adapted_plan["steps"], current_state)
        elif adaptation_type == "modal_state_adaptation":
            adapted_plan["steps"] = self._adapt_steps_for_modal_state(adapted_plan["steps"], current_state)
        elif adaptation_type == "timing_adaptation":
            adapted_plan["steps"] = self._adapt_steps_for_timing(adapted_plan["steps"])
        elif adaptation_type == "blocking_modal_adaptation":
            adapted_plan["steps"] = self._insert_modal_dismissal_steps(adapted_plan["steps"], current_state)
        
        # Update metadata
        adapted_plan["metadata"]["adaptation_history"] = adaptation_needed
        adapted_plan["metadata"]["adapted_from"] = self.current_plan["plan_id"]
        
        return adapted_plan
    
    def _adapt_steps_for_ui_changes(self, steps: List[Dict], current_state: Dict) -> List[Dict]:
        """Adapt steps when UI elements have changed."""
        adapted_steps = []
        available_elements = [elem.get("text", "") for elem in current_state.get("ui_elements", [])]
        
        for step in steps:
            adapted_step = step.copy()
            target = step.get("target", "")
            
            # Try to find alternative target if original not available
            if target not in available_elements:
                alternative_target = self._find_alternative_target(target, available_elements)
                if alternative_target:
                    adapted_step["target"] = alternative_target
                    adapted_step["description"] += f" (adapted from {target})"
            
            adapted_steps.append(adapted_step)
        
        return adapted_steps
    
    def _find_alternative_target(self, original_target: str, available_elements: List[str]) -> Optional[str]:
        """Find alternative target element when original is not available."""
        # Simple similarity matching - could be enhanced with fuzzy matching
        original_lower = original_target.lower()
        
        for element in available_elements:
            element_lower = element.lower()
            if any(word in element_lower for word in original_lower.split()):
                return element
        
        return None
    
    def _generate_fallback_strategies(self, goal: str) -> List[Dict[str, Any]]:
        """Generate fallback strategies for the overall goal."""
        strategies = [
            {
                "strategy_id": "alternative_navigation",
                "description": "Use alternative navigation paths when primary path fails",
                "triggers": ["navigation_failure", "ui_element_missing"],
                "actions": ["try_menu_navigation", "use_search_function", "use_voice_commands"]
            },
            {
                "strategy_id": "modal_recovery",
                "description": "Recover from unexpected modal states",
                "triggers": ["blocking_modal", "permission_dialog", "error_popup"],
                "actions": ["dismiss_modal", "grant_permissions", "retry_action"]
            },
            {
                "strategy_id": "timeout_handling",
                "description": "Handle slow or unresponsive UI",
                "triggers": ["action_timeout", "loading_too_long"],
                "actions": ["increase_wait_time", "restart_app", "check_connectivity"]
            }
        ]
        
        return strategies
    
    def _get_app_specific_context(self, subgoal: Dict) -> Dict[str, Any]:
        """Get app-specific context for a subgoal."""
        return {
            "app_type": self.task_name.split("_")[0] if "_" in self.task_name else "generic",
            "context_variables": subgoal.get("state_dependencies", []),
            "ui_patterns": self._identify_ui_patterns(subgoal),
            "interaction_methods": self._get_interaction_methods(subgoal)
        }
    
    def _identify_adaptation_triggers(self, subgoal: Dict) -> List[str]:
        """Identify what conditions would trigger plan adaptation."""
        triggers = [
            "ui_element_changed",
            "modal_state_unexpected",
            "timeout_exceeded",
            "permission_required",
            "network_error"
        ]
        
        # Add subgoal-specific triggers
        if "wifi" in subgoal.get("description", "").lower():
            triggers.extend(["airplane_mode_detected", "wifi_hardware_disabled"])
        elif "alarm" in subgoal.get("description", "").lower():
            triggers.extend(["do_not_disturb_active", "clock_permission_denied"])
        
        return triggers
    
    def _identify_ui_patterns(self, subgoal: Dict) -> List[str]:
        """Identify UI patterns relevant to this subgoal."""
        patterns = ["standard_navigation", "tap_interactions"]
        
        description = subgoal.get("description", "").lower()
        if "toggle" in description:
            patterns.append("toggle_switch_pattern")
        if "settings" in description:
            patterns.append("settings_menu_pattern")
        if "alarm" in description:
            patterns.append("time_picker_pattern")
        
        return patterns
    
    def _get_interaction_methods(self, subgoal: Dict) -> List[str]:
        """Get available interaction methods for this subgoal."""
        methods = ["touch", "tap"]
        
        actions = subgoal.get("required_actions", [])
        if any("toggle" in action for action in actions):
            methods.extend(["swipe", "long_press"])
        if any("type" in action or "enter" in action for action in actions):
            methods.append("keyboard_input")
        
        return methods
    
    def _adapt_steps_for_modal_state(self, steps: List[Dict], current_state: Dict) -> List[Dict]:
        """Adapt steps when modal state doesn't match expectations."""
        adapted_steps = []
        detected_modal = self._detect_current_modal(current_state.get("ui_elements", []))
        
        # Insert modal correction steps at the beginning
        if detected_modal != "unknown":
            modal_correction_step = {
                "step_id": 0,
                "action": "handle_modal_state",
                "target": detected_modal,
                "description": f"Handle unexpected modal state: {detected_modal}",
                "expected_result": "Modal state corrected",
                "validation_criteria": ["Target modal state achieved"],
                "modal_correction": True
            }
            adapted_steps.append(modal_correction_step)
        
        # Adjust remaining steps
        for step in steps:
            adapted_step = step.copy()
            adapted_step["step_id"] += 1  # Shift step IDs
            adapted_steps.append(adapted_step)
        
        return adapted_steps
    
    def _adapt_steps_for_timing(self, steps: List[Dict]) -> List[Dict]:
        """Adapt steps for timing issues by increasing wait times."""
        adapted_steps = []
        
        for step in steps:
            adapted_step = step.copy()
            
            # Add longer wait times
            if "retry_strategy" in adapted_step:
                adapted_step["retry_strategy"]["retry_delay"] *= 2
                adapted_step["retry_strategy"]["max_retries"] += 1
            
            # Add explicit wait steps before critical actions
            if step.get("action") in ["toggle", "tap", "navigate"]:
                wait_step = {
                    "step_id": step["step_id"] - 0.5,
                    "action": "wait",
                    "target": "ui_stabilization",
                    "description": f"Wait for UI stabilization before {step['action']}",
                    "expected_result": "UI ready for interaction",
                    "validation_criteria": ["UI elements responsive"]
                }
                adapted_steps.append(wait_step)
            
            adapted_steps.append(adapted_step)
        
        return adapted_steps
    
    def _insert_modal_dismissal_steps(self, steps: List[Dict], current_state: Dict) -> List[Dict]:
        """Insert steps to dismiss blocking modals."""
        blocking_elements = self._detect_blocking_elements(current_state.get("ui_elements", []))
        
        dismissal_steps = []
        for i, blocking_element in enumerate(blocking_elements):
            dismissal_step = {
                "step_id": -(i + 1),  # Negative IDs for pre-steps
                "action": "dismiss_modal",
                "target": blocking_element,
                "description": f"Dismiss blocking modal: {blocking_element}",
                "expected_result": "Modal dismissed successfully",
                "validation_criteria": ["Modal no longer visible", "Main UI accessible"],
                "blocking_modal_handler": True
            }
            dismissal_steps.append(dismissal_step)
        
        # Combine dismissal steps with original steps
        return dismissal_steps + steps
    
    def _create_wifi_plan(self) -> List[Dict[str, Any]]:
        """Create WiFi-specific test plan."""
        return [
            {
                "step_id": 1,
                "action": "navigate",
                "target": "Settings",
                "description": "Open Android Settings from the home screen",
                "expected_result": "Settings app opens successfully",
                "validation_criteria": ["Settings title visible", "Menu options displayed"]
            },
            {
                "step_id": 2,
                "action": "tap",
                "target": "Network & internet",
                "description": "Navigate to Network & internet section",
                "expected_result": "Network settings screen appears",
                "validation_criteria": ["Wi-Fi option visible", "Network options displayed"]
            },
            {
                "step_id": 3,
                "action": "tap",
                "target": "Wi-Fi",
                "description": "Enter Wi-Fi settings",
                "expected_result": "Wi-Fi settings screen opens",
                "validation_criteria": ["Wi-Fi toggle visible", "Available networks section visible"]
            },
            {
                "step_id": 4,
                "action": "toggle",
                "target": "Wi-Fi switch",
                "description": "Toggle Wi-Fi ON and verify connection",
                "expected_result": "Wi-Fi enables and shows available networks",
                "validation_criteria": ["Wi-Fi status shows ON", "Available networks populate"]
            },
            {
                "step_id": 5,
                "action": "toggle",
                "target": "Wi-Fi switch",
                "description": "Toggle Wi-Fi OFF and verify disconnection",
                "expected_result": "Wi-Fi disables and networks disappear",
                "validation_criteria": ["Wi-Fi status shows OFF", "No connected network shown"]
            }
        ]
    
    def _create_alarm_plan(self) -> List[Dict[str, Any]]:
        """Create alarm/clock-specific test plan."""
        return [
            {
                "step_id": 1,
                "action": "navigate",
                "target": "Clock app",
                "description": "Open Clock application",
                "expected_result": "Clock app launches successfully",
                "validation_criteria": ["Clock interface visible", "Alarm tab accessible"]
            },
            {
                "step_id": 2,
                "action": "tap",
                "target": "Alarm tab",
                "description": "Navigate to alarm section",
                "expected_result": "Alarm list screen appears",
                "validation_criteria": ["Add alarm button visible", "Existing alarms listed"]
            },
            {
                "step_id": 3,
                "action": "tap",
                "target": "Add alarm",
                "description": "Create new alarm",
                "expected_result": "Alarm creation interface opens",
                "validation_criteria": ["Time picker visible", "Save option available"]
            },
            {
                "step_id": 4,
                "action": "set_time",
                "target": "Time picker",
                "description": "Set alarm time and save",
                "expected_result": "Alarm is created and saved",
                "validation_criteria": ["Alarm appears in list", "Time correctly set"]
            },
            {
                "step_id": 5,
                "action": "toggle",
                "target": "Alarm switch",
                "description": "Enable/disable alarm and verify status",
                "expected_result": "Alarm status changes correctly",
                "validation_criteria": ["Switch state matches expectation", "Alarm time updated"]
            }
        ]
    
    def _create_email_plan(self) -> List[Dict[str, Any]]:
        """Create email-specific test plan."""
        return [
            {
                "step_id": 1,
                "action": "navigate",
                "target": "Email app",
                "description": "Open email application",
                "expected_result": "Email app launches successfully",
                "validation_criteria": ["Inbox visible", "Search option available"]
            },
            {
                "step_id": 2,
                "action": "tap",
                "target": "Search",
                "description": "Access email search functionality",
                "expected_result": "Search interface opens",
                "validation_criteria": ["Search box visible", "Keyboard appears"]
            },
            {
                "step_id": 3,
                "action": "type",
                "target": "Search box",
                "description": "Enter search query",
                "expected_result": "Search query is entered",
                "validation_criteria": ["Text appears in search box", "Search suggestions may appear"]
            },
            {
                "step_id": 4,
                "action": "tap",
                "target": "Search button",
                "description": "Execute email search",
                "expected_result": "Search results are displayed",
                "validation_criteria": ["Results list appears", "Relevant emails shown"]
            },
            {
                "step_id": 5,
                "action": "tap",
                "target": "First result",
                "description": "Open first email from search results",
                "expected_result": "Email opens successfully",
                "validation_criteria": ["Email content visible", "Reply/Forward options available"]
            }
        ]
    
    def _create_generic_plan(self, goal: str) -> List[Dict[str, Any]]:
        """Create generic test plan for unknown tasks."""
        return [
            {
                "step_id": 1,
                "action": "navigate",
                "target": "Target app",
                "description": f"Open application for goal: {goal}",
                "expected_result": "Application launches successfully",
                "validation_criteria": ["App interface visible", "Main features accessible"]
            },
            {
                "step_id": 2,
                "action": "explore",
                "target": "Main interface",
                "description": "Explore main application features",
                "expected_result": "Key features are discoverable",
                "validation_criteria": ["Navigation elements visible", "Primary actions available"]
            },
            {
                "step_id": 3,
                "action": "test",
                "target": "Primary feature",
                "description": "Test main functionality",
                "expected_result": "Primary feature works as expected",
                "validation_criteria": ["Feature responds correctly", "No errors occur"]
            }
        ]
    
    def get_plan_summary(self) -> Optional[str]:
        """Get a summary of the current plan."""
        if not self.current_plan:
            return None
            
        summary = f"Plan: {self.current_plan['goal']}\n"
        summary += f"Task: {self.current_plan['task_name']}\n"
        summary += f"Steps: {len(self.current_plan['steps'])}\n"
        summary += f"Estimated Duration: {self.current_plan['estimated_duration']} seconds\n\n"
        
        for step in self.current_plan['steps']:
            summary += f"Step {step['step_id']}: {step['description']}\n"
            
        return summary

def generate_test_plan(goal: str, task_name: str = "settings_wifi") -> str:
    """Legacy function for backward compatibility."""
    planner = PlannerAgent(task_name)
    plan = planner.generate_test_plan(goal)
    return planner.get_plan_summary()

if __name__ == "__main__":
    # Test the enhanced planner
    planner = PlannerAgent("settings_wifi")
    goal = "Test turning Wi-Fi on and off in Android settings"
    
    plan = planner.generate_test_plan(goal)
    print("Generated Enhanced Test Plan:")
    print(json.dumps(plan, indent=2))
    
    print("\nPlan Summary:")
    print(planner.get_plan_summary())

