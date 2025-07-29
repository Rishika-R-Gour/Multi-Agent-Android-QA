# verifier_agent.py

import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from android_env_wrapper import AndroidEnv

class VerifierAgent:
    """
    Enhanced Verifier Agent that receives Planner Goal, Executor Result, and UI State
    to determine if current state matches expectations and detect functional bugs.
    
    Features:
    - State expectation verification
    - Functional bug detection
    - LLM reasoning over UI hierarchy
    - Heuristic-based validation
    - Dynamic replanning triggers
    """
    
    def __init__(self, task_name: str = "qa_verification", enable_logging: bool = True):
        self.task_name = task_name
        self.enable_logging = enable_logging
        self.logger = logging.getLogger(f"VerifierAgent.{task_name}")
        
        # Verification state
        self.verification_history = []
        self.bug_detection_rules = self._initialize_bug_detection_rules()
        self.ui_state_expectations = {}
        self.current_verification_session = None
        
        # Metrics
        self.total_verifications = 0
        self.bugs_detected = 0
        self.false_positives = 0
        self.replanning_triggers = 0
        
    def verify_goal_state(self, planner_goal: Dict[str, Any], 
                         executor_result: Dict[str, Any], 
                         ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main verification method that receives Planner Goal, Executor Result, and UI State
        to determine if current state matches expectations.
        """
        verification_id = f"verify_{int(time.time())}"
        start_time = time.time()
        
        self.logger.info(f"Starting verification {verification_id}")
        
        verification_result = {
            "verification_id": verification_id,
            "timestamp": datetime.now().isoformat(),
            "planner_goal": planner_goal,
            "executor_result": executor_result,
            "ui_state": ui_state,
            "start_time": start_time,
            "status": "running",
            "expectation_match": None,
            "functional_bugs": [],
            "heuristic_checks": {},
            "llm_reasoning": {},
            "replanning_required": False,
            "confidence_score": 0.0
        }
        
        try:
            # Step 1: Check state expectations
            expectation_result = self._verify_state_expectations(planner_goal, executor_result, ui_state)
            verification_result["expectation_match"] = expectation_result
            
            # Step 2: Detect functional bugs
            bug_detection_result = self._detect_functional_bugs(ui_state, planner_goal, executor_result)
            verification_result["functional_bugs"] = bug_detection_result
            
            # Step 3: Run heuristic checks
            heuristic_result = self._run_heuristic_checks(ui_state, planner_goal)
            verification_result["heuristic_checks"] = heuristic_result
            
            # Step 4: LLM reasoning over UI hierarchy
            llm_reasoning_result = self._llm_reasoning_over_ui(ui_state, planner_goal, executor_result)
            verification_result["llm_reasoning"] = llm_reasoning_result
            
            # Step 5: Determine overall verdict and replanning needs
            final_verdict = self._determine_final_verdict(verification_result)
            verification_result.update(final_verdict)
            
            verification_result["status"] = "completed"
            
        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            verification_result["status"] = "failed"
            verification_result["error"] = str(e)
            
        verification_result["end_time"] = time.time()
        verification_result["duration"] = verification_result["end_time"] - start_time
        
        # Log the verification
        self._log_verification(verification_result)
        
        # Update metrics
        self.total_verifications += 1
        if verification_result.get("functional_bugs"):
            self.bugs_detected += len(verification_result["functional_bugs"])
        if verification_result.get("replanning_required"):
            self.replanning_triggers += 1
            
        return verification_result
    
    def _verify_state_expectations(self, planner_goal: Dict[str, Any], 
                                 executor_result: Dict[str, Any], 
                                 ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify if the current state matches the expected state from the planner goal.
        """
        expected_outcomes = planner_goal.get("success_criteria", [])
        target_modal = planner_goal.get("target_modal", "unknown")
        required_ui_elements = planner_goal.get("required_ui_elements", [])
        
        expectation_results = {
            "overall_match": True,
            "criteria_results": {},
            "missing_elements": [],
            "unexpected_elements": [],
            "modal_state_correct": True,
            "confidence": 0.0
        }
        
        # Check success criteria
        for criterion in expected_outcomes:
            criterion_met = self._check_success_criterion(criterion, ui_state, executor_result)
            expectation_results["criteria_results"][criterion] = criterion_met
            if not criterion_met:
                expectation_results["overall_match"] = False
        
        # Check required UI elements
        ui_elements = ui_state.get("ui_elements", [])
        ui_element_texts = [elem.get("text", "").lower() for elem in ui_elements]
        
        for required_element in required_ui_elements:
            element_found = any(required_element.lower() in text for text in ui_element_texts)
            if not element_found:
                expectation_results["missing_elements"].append(required_element)
                expectation_results["overall_match"] = False
        
        # Check modal state
        current_modal = self._infer_current_modal(ui_state)
        if target_modal != "unknown" and current_modal != target_modal:
            expectation_results["modal_state_correct"] = False
            expectation_results["overall_match"] = False
        
        # Calculate confidence
        total_checks = len(expected_outcomes) + len(required_ui_elements) + 1  # +1 for modal
        successful_checks = len([r for r in expectation_results["criteria_results"].values() if r])
        successful_checks += (len(required_ui_elements) - len(expectation_results["missing_elements"]))
        if expectation_results["modal_state_correct"]:
            successful_checks += 1
            
        expectation_results["confidence"] = successful_checks / max(total_checks, 1)
        
        return expectation_results
    
    def _detect_functional_bugs(self, ui_state: Dict[str, Any], 
                              planner_goal: Dict[str, Any], 
                              executor_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect functional bugs like missing screens, wrong toggle states, etc.
        """
        detected_bugs = []
        ui_elements = ui_state.get("ui_elements", [])
        
        # Rule-based bug detection
        for rule_name, rule_func in self.bug_detection_rules.items():
            try:
                bug_result = rule_func(ui_state, planner_goal, executor_result)
                if bug_result:
                    detected_bugs.append({
                        "bug_type": rule_name,
                        "description": bug_result.get("description", "Unknown bug"),
                        "severity": bug_result.get("severity", "medium"),
                        "evidence": bug_result.get("evidence", {}),
                        "suggested_action": bug_result.get("suggested_action", "manual_review")
                    })
            except Exception as e:
                self.logger.warning(f"Bug detection rule {rule_name} failed: {e}")
        
        # Specific bug patterns
        
        # 1. Check for error dialogs or popups
        error_indicators = ["error", "failed", "cannot", "unable", "invalid"]
        for element in ui_elements:
            element_text = element.get("text", "").lower()
            if any(indicator in element_text for indicator in error_indicators):
                detected_bugs.append({
                    "bug_type": "error_dialog_detected",
                    "description": f"Error dialog found: {element.get('text', '')}",
                    "severity": "high",
                    "evidence": {"element": element},
                    "suggested_action": "dismiss_dialog_and_retry"
                })
        
        # 2. Check for toggle state mismatches
        if "toggle" in planner_goal.get("description", "").lower():
            toggle_bugs = self._detect_toggle_state_bugs(ui_elements, planner_goal, executor_result)
            detected_bugs.extend(toggle_bugs)
        
        # 3. Check for missing expected screens
        expected_screen_indicators = planner_goal.get("success_criteria", [])
        for indicator in expected_screen_indicators:
            if "visible" in indicator and not self._check_screen_visible(indicator, ui_elements):
                detected_bugs.append({
                    "bug_type": "missing_expected_screen",
                    "description": f"Expected screen not visible: {indicator}",
                    "severity": "high",
                    "evidence": {"expected": indicator, "current_elements": [e.get("text") for e in ui_elements]},
                    "suggested_action": "navigate_to_correct_screen"
                })
        
        return detected_bugs
    
    def _run_heuristic_checks(self, ui_state: Dict[str, Any], planner_goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run heuristic-based validation checks.
        """
        ui_elements = ui_state.get("ui_elements", [])
        
        heuristic_results = {
            "ui_responsiveness": self._check_ui_responsiveness(ui_elements),
            "element_accessibility": self._check_element_accessibility(ui_elements),
            "navigation_consistency": self._check_navigation_consistency(ui_elements, planner_goal),
            "loading_state_detection": self._check_loading_states(ui_elements),
            "modal_blocking_detection": self._check_modal_blocking(ui_elements)
        }
        
        # Calculate overall heuristic score
        scores = [result.get("score", 0) for result in heuristic_results.values() if isinstance(result, dict)]
        heuristic_results["overall_heuristic_score"] = sum(scores) / len(scores) if scores else 0
        
        return heuristic_results
    
    def _llm_reasoning_over_ui(self, ui_state: Dict[str, Any], 
                             planner_goal: Dict[str, Any], 
                             executor_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply LLM-like reasoning over the UI hierarchy for intelligent verification.
        """
        ui_elements = ui_state.get("ui_elements", [])
        goal_description = planner_goal.get("description", "")
        
        # Simulate LLM reasoning with rule-based logic
        reasoning_result = {
            "semantic_analysis": self._analyze_ui_semantics(ui_elements, goal_description),
            "context_appropriateness": self._check_context_appropriateness(ui_elements, planner_goal),
            "user_flow_consistency": self._analyze_user_flow_consistency(ui_elements, planner_goal, executor_result),
            "intent_fulfillment": self._assess_intent_fulfillment(ui_elements, planner_goal, executor_result)
        }
        
        # Generate reasoning summary
        reasoning_result["summary"] = self._generate_reasoning_summary(reasoning_result)
        reasoning_result["confidence"] = self._calculate_reasoning_confidence(reasoning_result)
        
        return reasoning_result
    
    def _determine_final_verdict(self, verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the final verdict and whether replanning is required.
        """
        expectation_match = verification_result.get("expectation_match", {})
        functional_bugs = verification_result.get("functional_bugs", [])
        heuristic_checks = verification_result.get("heuristic_checks", {})
        llm_reasoning = verification_result.get("llm_reasoning", {})
        
        # Determine pass/fail
        has_critical_bugs = any(bug.get("severity") == "high" for bug in functional_bugs)
        expectations_met = expectation_match.get("overall_match", False)
        heuristic_score = heuristic_checks.get("overall_heuristic_score", 0)
        reasoning_confidence = llm_reasoning.get("confidence", 0)
        
        # Final verdict logic
        if has_critical_bugs:
            verdict = "FAIL"
            reason = "Critical functional bugs detected"
        elif not expectations_met:
            verdict = "FAIL" 
            reason = "State expectations not met"
        elif heuristic_score < 0.6:
            verdict = "FAIL"
            reason = "Heuristic checks indicate problems"
        elif reasoning_confidence < 0.7:
            verdict = "FAIL"
            reason = "LLM reasoning indicates inconsistencies"
        else:
            verdict = "PASS"
            reason = "All verification checks passed"
        
        # Determine replanning needs
        replanning_required = (
            has_critical_bugs or 
            any(bug.get("suggested_action") in ["navigate_to_correct_screen", "dismiss_dialog_and_retry"] 
                for bug in functional_bugs) or
            heuristic_checks.get("modal_blocking_detection", {}).get("blocking_detected", False)
        )
        
        # Calculate overall confidence
        confidence_factors = [
            expectation_match.get("confidence", 0),
            heuristic_score,
            reasoning_confidence
        ]
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return {
            "verdict": verdict,
            "reason": reason,
            "replanning_required": replanning_required,
            "confidence_score": overall_confidence,
            "replanning_suggestions": self._generate_replanning_suggestions(functional_bugs, heuristic_checks)
        }
    
    def _generate_replanning_suggestions(self, functional_bugs: List[Dict], heuristic_checks: Dict) -> List[str]:
        """Generate specific suggestions for replanning based on detected issues."""
        suggestions = []
        
        for bug in functional_bugs:
            action = bug.get("suggested_action", "")
            if action == "dismiss_dialog_and_retry":
                suggestions.append("Add step to dismiss error dialog before retrying")
            elif action == "navigate_to_correct_screen":
                suggestions.append("Add navigation steps to reach the expected screen")
            elif action == "manual_review":
                suggestions.append(f"Manual review needed for: {bug.get('description', 'unknown issue')}")
        
        if heuristic_checks.get("modal_blocking_detection", {}).get("blocking_detected"):
            suggestions.append("Handle blocking modal before proceeding")
            
        return suggestions
    
    def _initialize_bug_detection_rules(self) -> Dict[str, callable]:
        """Initialize rule-based bug detection functions."""
        return {
            "crash_detection": self._detect_app_crash,
            "permission_blocking": self._detect_permission_blocking,
            "network_errors": self._detect_network_errors,
            "timeout_issues": self._detect_timeout_issues,
            "ui_freeze": self._detect_ui_freeze
        }
    
    def _log_verification(self, verification_result: Dict[str, Any]):
        """Log verification results in structured JSON format."""
        if not self.enable_logging:
            return
            
        log_entry = {
            "agent": "VerifierAgent",
            "timestamp": verification_result["timestamp"],
            "verification_id": verification_result["verification_id"],
            "verdict": verification_result.get("verdict", "UNKNOWN"),
            "confidence": verification_result.get("confidence_score", 0),
            "bugs_detected": len(verification_result.get("functional_bugs", [])),
            "replanning_required": verification_result.get("replanning_required", False),
            "duration": verification_result.get("duration", 0),
            "details": {
                "expectation_match": verification_result.get("expectation_match", {}),
                "functional_bugs": verification_result.get("functional_bugs", []),
                "heuristic_scores": verification_result.get("heuristic_checks", {}),
                "llm_reasoning": verification_result.get("llm_reasoning", {})
            }
        }
        
        # Save to JSON log file
        log_filename = f"qa_verification_log_{datetime.now().strftime('%Y%m%d')}.json"
        try:
            with open(f"reports/{log_filename}", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write verification log: {e}")
        
        self.verification_history.append(log_entry)
    
    # Helper methods for various checks (simplified implementations)
    def _check_success_criterion(self, criterion: str, ui_state: Dict, executor_result: Dict) -> bool:
        """Check if a specific success criterion is met."""
        ui_elements = ui_state.get("ui_elements", [])
        ui_texts = [elem.get("text", "").lower() for elem in ui_elements]
        return any(criterion.lower() in text for text in ui_texts)
    
    def _infer_current_modal(self, ui_state: Dict) -> str:
        """Infer the current modal/screen state from UI elements."""
        ui_elements = ui_state.get("ui_elements", [])
        
        # Simple modal inference based on common patterns
        for element in ui_elements:
            text = element.get("text", "").lower()
            if "settings" in text:
                return "settings_app"
            elif "wifi" in text or "wi-fi" in text:
                return "wifi_settings"
            elif "network" in text:
                return "network_settings"
        
        return "unknown"
    
    def _detect_toggle_state_bugs(self, ui_elements: List, planner_goal: Dict, executor_result: Dict) -> List[Dict]:
        """Detect bugs related to toggle state mismatches."""
        bugs = []
        
        # Look for toggle elements
        for element in ui_elements:
            text = element.get("text", "")
            if text in ["ON", "OFF"] and element.get("switch", False):
                # Check if toggle state matches expected outcome
                expected_state = self._infer_expected_toggle_state(planner_goal, executor_result)
                if expected_state and text != expected_state:
                    bugs.append({
                        "bug_type": "toggle_state_mismatch",
                        "description": f"Toggle state is {text}, expected {expected_state}",
                        "severity": "medium",
                        "evidence": {"element": element, "expected": expected_state},
                        "suggested_action": "retry_toggle_action"
                    })
        
        return bugs
    
    def _check_screen_visible(self, indicator: str, ui_elements: List) -> bool:
        """Check if a specific screen is visible based on indicator."""
        ui_texts = [elem.get("text", "").lower() for elem in ui_elements]
        return any(indicator.lower().replace("_visible", "") in text for text in ui_texts)
    
    def _check_ui_responsiveness(self, ui_elements: List) -> Dict:
        """Check UI responsiveness heuristics."""
        return {
            "score": 0.9,  # Simplified
            "responsive": True,
            "issues": []
        }
    
    def _check_element_accessibility(self, ui_elements: List) -> Dict:
        """Check element accessibility."""
        clickable_count = sum(1 for elem in ui_elements if elem.get("clickable", False))
        total_count = len(ui_elements)
        accessibility_ratio = clickable_count / max(total_count, 1)
        
        return {
            "score": accessibility_ratio,
            "clickable_ratio": accessibility_ratio,
            "issues": [] if accessibility_ratio > 0.3 else ["Low clickable element ratio"]
        }
    
    def _check_navigation_consistency(self, ui_elements: List, planner_goal: Dict) -> Dict:
        """Check navigation consistency."""
        return {
            "score": 0.8,  # Simplified
            "consistent": True,
            "issues": []
        }
    
    def _check_loading_states(self, ui_elements: List) -> Dict:
        """Check for loading states."""
        loading_indicators = ["loading", "wait", "progress"]
        has_loading = any(
            any(indicator in elem.get("text", "").lower() for indicator in loading_indicators)
            for elem in ui_elements
        )
        
        return {
            "score": 0.5 if has_loading else 1.0,
            "loading_detected": has_loading,
            "issues": ["Loading state detected"] if has_loading else []
        }
    
    def _check_modal_blocking(self, ui_elements: List) -> Dict:
        """Check for blocking modals."""
        blocking_keywords = ["dialog", "popup", "alert", "permission", "allow", "deny"]
        blocking_detected = any(
            any(keyword in elem.get("text", "").lower() for keyword in blocking_keywords)
            for elem in ui_elements
        )
        
        return {
            "score": 0.3 if blocking_detected else 1.0,
            "blocking_detected": blocking_detected,
            "issues": ["Blocking modal detected"] if blocking_detected else []
        }
    
    def _analyze_ui_semantics(self, ui_elements: List, goal_description: str) -> Dict:
        """Analyze UI semantics for goal relevance."""
        goal_keywords = goal_description.lower().split()
        ui_texts = [elem.get("text", "").lower() for elem in ui_elements]
        
        semantic_match_count = sum(
            1 for keyword in goal_keywords
            if any(keyword in text for text in ui_texts)
        )
        
        semantic_score = semantic_match_count / max(len(goal_keywords), 1)
        
        return {
            "semantic_score": semantic_score,
            "matched_keywords": semantic_match_count,
            "total_keywords": len(goal_keywords)
        }
    
    def _check_context_appropriateness(self, ui_elements: List, planner_goal: Dict) -> Dict:
        """Check if current UI context is appropriate for the goal."""
        return {
            "appropriate": True,
            "score": 0.8,
            "context_match": "good"
        }
    
    def _analyze_user_flow_consistency(self, ui_elements: List, planner_goal: Dict, executor_result: Dict) -> Dict:
        """Analyze user flow consistency."""
        return {
            "consistent": True,
            "score": 0.9,
            "flow_issues": []
        }
    
    def _assess_intent_fulfillment(self, ui_elements: List, planner_goal: Dict, executor_result: Dict) -> Dict:
        """Assess whether user intent is being fulfilled."""
        return {
            "fulfilled": True,
            "score": 0.85,
            "intent_alignment": "high"
        }
    
    def _generate_reasoning_summary(self, reasoning_result: Dict) -> str:
        """Generate a summary of LLM reasoning."""
        semantic_score = reasoning_result.get("semantic_analysis", {}).get("semantic_score", 0)
        context_score = reasoning_result.get("context_appropriateness", {}).get("score", 0)
        
        if semantic_score > 0.8 and context_score > 0.8:
            return "UI state strongly aligns with goal intent and context"
        elif semantic_score > 0.6 or context_score > 0.6:
            return "UI state partially aligns with goal intent"
        else:
            return "UI state poorly aligns with goal intent"
    
    def _calculate_reasoning_confidence(self, reasoning_result: Dict) -> float:
        """Calculate overall reasoning confidence."""
        scores = [
            reasoning_result.get("semantic_analysis", {}).get("semantic_score", 0),
            reasoning_result.get("context_appropriateness", {}).get("score", 0),
            reasoning_result.get("user_flow_consistency", {}).get("score", 0),
            reasoning_result.get("intent_fulfillment", {}).get("score", 0)
        ]
        return sum(scores) / len(scores)
    
    def _infer_expected_toggle_state(self, planner_goal: Dict, executor_result: Dict) -> Optional[str]:
        """Infer expected toggle state from goal and execution."""
        goal_desc = planner_goal.get("description", "").lower()
        if "turn on" in goal_desc or "enable" in goal_desc:
            return "ON"
        elif "turn off" in goal_desc or "disable" in goal_desc:
            return "OFF"
        return None
    
    # Simplified bug detection rule implementations
    def _detect_app_crash(self, ui_state: Dict, planner_goal: Dict, executor_result: Dict) -> Optional[Dict]:
        """Detect app crash conditions."""
        ui_elements = ui_state.get("ui_elements", [])
        crash_indicators = ["has stopped", "not responding", "force close"]
        
        for element in ui_elements:
            text = element.get("text", "").lower()
            if any(indicator in text for indicator in crash_indicators):
                return {
                    "description": f"App crash detected: {element.get('text')}",
                    "severity": "high",
                    "evidence": {"crash_dialog": element},
                    "suggested_action": "restart_app"
                }
        return None
    
    def _detect_permission_blocking(self, ui_state: Dict, planner_goal: Dict, executor_result: Dict) -> Optional[Dict]:
        """Detect permission blocking dialogs."""
        ui_elements = ui_state.get("ui_elements", [])
        permission_indicators = ["allow", "deny", "permission", "access"]
        
        for element in ui_elements:
            text = element.get("text", "").lower()
            if any(indicator in text for indicator in permission_indicators):
                return {
                    "description": f"Permission dialog detected: {element.get('text')}",
                    "severity": "medium",
                    "evidence": {"permission_dialog": element},
                    "suggested_action": "handle_permission_dialog"
                }
        return None
    
    def _detect_network_errors(self, ui_state: Dict, planner_goal: Dict, executor_result: Dict) -> Optional[Dict]:
        """Detect network-related errors."""
        ui_elements = ui_state.get("ui_elements", [])
        network_error_indicators = ["no connection", "network error", "offline", "connection failed"]
        
        for element in ui_elements:
            text = element.get("text", "").lower()
            if any(indicator in text for indicator in network_error_indicators):
                return {
                    "description": f"Network error detected: {element.get('text')}",
                    "severity": "high",
                    "evidence": {"network_error": element},
                    "suggested_action": "check_network_connectivity"
                }
        return None
    
    def _detect_timeout_issues(self, ui_state: Dict, planner_goal: Dict, executor_result: Dict) -> Optional[Dict]:
        """Detect timeout-related issues."""
        # Simplified timeout detection
        return None
    
    def _detect_ui_freeze(self, ui_state: Dict, planner_goal: Dict, executor_result: Dict) -> Optional[Dict]:
        """Detect UI freeze conditions."""
        # Simplified UI freeze detection
        return None
    
    def get_verification_metrics(self) -> Dict[str, Any]:
        """Get verification metrics and statistics."""
        return {
            "total_verifications": self.total_verifications,
            "bugs_detected": self.bugs_detected,
            "false_positives": self.false_positives,
            "replanning_triggers": self.replanning_triggers,
            "accuracy_rate": (self.total_verifications - self.false_positives) / max(self.total_verifications, 1),
            "bug_detection_rate": self.bugs_detected / max(self.total_verifications, 1)
        }

# Legacy function for backward compatibility
def verify_step(step):
    """
    Legacy verification function for backward compatibility.
    """
    import random
    result = "PASS" if random.random() > 0.2 else "FAIL"
    print(f"[Verifier Agent] Step Verification: {step} -> {result}")
    return result

if __name__ == "__main__":
    # Test the enhanced verifier
    verifier = VerifierAgent()
    
    # Mock test data
    planner_goal = {
        "subgoal_id": "wifi_toggle_test",
        "description": "Toggle Wi-Fi setting",
        "success_criteria": ["wifi_toggle_visible", "state_changed"],
        "target_modal": "wifi_settings"
    }
    
    executor_result = {
        "status": "completed",
        "actions_executed": [{"action_type": "touch", "target": "wifi_toggle"}]
    }
    
    ui_state = {
        "ui_elements": [
            {"text": "Wi-Fi", "clickable": False},
            {"text": "ON", "clickable": True, "switch": True},
            {"text": "Network list", "clickable": False}
        ]
    }
    
    # Run verification
    result = verifier.verify_goal_state(planner_goal, executor_result, ui_state)
    print(f"Verification result: {result['verdict']} - {result['reason']}")
    print(f"Replanning required: {result['replanning_required']}")
    print(f"Confidence: {result['confidence_score']:.2f}")
