# supervisor_agent.py

import os
import json
import time
import base64
import io
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

class VisualTraceRecorder:
    """
    Records visual traces of test execution including screenshots and UI states.
    Implements env.render(mode='rgb_array') functionality for visual recording.
    """
    
    def __init__(self, trace_dir: str = "traces"):
        self.trace_dir = trace_dir
        self.current_trace = None
        self.trace_id = None
        self.logger = logging.getLogger("VisualTraceRecorder")
        
        # Ensure trace directory exists
        os.makedirs(trace_dir, exist_ok=True)
        
    def start_trace(self, test_goal: str, task_name: str) -> str:
        """Start recording a new visual trace."""
        self.trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_name}"
        trace_path = os.path.join(self.trace_dir, self.trace_id)
        os.makedirs(trace_path, exist_ok=True)
        
        self.current_trace = {
            "trace_id": self.trace_id,
            "test_goal": test_goal,
            "task_name": task_name,
            "start_time": time.time(),
            "frames": [],
            "agent_actions": [],
            "ui_states": [],
            "metadata": {
                "trace_path": trace_path,
                "frame_count": 0,
                "total_duration": 0
            }
        }
        
        self.logger.info(f"Started visual trace recording: {self.trace_id}")
        return self.trace_id
    
    def render(self, env_state: Dict[str, Any], mode: str = 'rgb_array') -> Union[Any, str]:
        """
        Render environment state in specified mode.
        
        Args:
            env_state: Current environment state with pixels and UI elements
            mode: Rendering mode ('rgb_array', 'human', 'save')
            
        Returns:
            Rendered image as numpy array or saved file path
        """
        if not self.current_trace:
            self.logger.warning("No active trace. Call start_trace() first.")
            return None
            
        pixels = env_state.get("pixels")
        ui_elements = env_state.get("ui_elements", [])
        
        if pixels is None:
            self.logger.warning("No pixels in environment state")
            return None
            
        # Convert to numpy array if needed
        if NUMPY_AVAILABLE and not isinstance(pixels, np.ndarray):
            if isinstance(pixels, list):
                pixels = np.array(pixels, dtype=np.uint8)
        
        frame_id = self.current_trace["metadata"]["frame_count"]
        timestamp = time.time()
        
        if mode == 'rgb_array':
            # Return raw numpy array
            return pixels
            
        elif mode == 'human' or mode == 'save':
            # Save annotated screenshot with UI elements marked
            annotated_image = self._annotate_screenshot(pixels, ui_elements)
            
            # Save frame
            trace_path = self.current_trace["metadata"]["trace_path"]
            frame_filename = f"frame_{frame_id:04d}.png"
            frame_path = os.path.join(trace_path, frame_filename)
            
            if PIL_AVAILABLE and annotated_image is not None:
                if isinstance(annotated_image, np.ndarray):
                    Image.fromarray(annotated_image).save(frame_path)
                else:
                    annotated_image.save(frame_path)
            elif NUMPY_AVAILABLE:
                # Fallback: save raw pixels
                Image.fromarray(pixels).save(frame_path)
            
            # Record frame metadata
            self.current_trace["frames"].append({
                "frame_id": frame_id,
                "timestamp": timestamp,
                "file_path": frame_path,
                "ui_element_count": len(ui_elements),
                "dimensions": pixels.shape if hasattr(pixels, 'shape') else None
            })
            
            self.current_trace["metadata"]["frame_count"] += 1
            
            return frame_path if mode == 'save' else annotated_image
    
    def _annotate_screenshot(self, pixels: Any, ui_elements: List[Dict]) -> Optional[Any]:
        """Annotate screenshot with UI element bounding boxes and labels."""
        if not NUMPY_AVAILABLE or not PIL_AVAILABLE:
            return pixels
            
        try:
            # Convert to PIL Image for annotation
            if isinstance(pixels, np.ndarray) and len(pixels.shape) == 3:
                img = Image.fromarray(pixels.astype(np.uint8))
            else:
                return pixels
                
            # Import drawing capabilities
            try:
                from PIL import ImageDraw, ImageFont
            except ImportError:
                return np.array(img)
            
            draw = ImageDraw.Draw(img)
            
            # Try to load a font
            try:
                font = ImageFont.truetype("Arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Draw UI element bounding boxes
            for i, element in enumerate(ui_elements):
                if "bounds" in element:
                    bounds = element["bounds"]
                    if len(bounds) >= 4:
                        x1, y1, x2, y2 = bounds[:4]
                        # Draw bounding box
                        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                        
                        # Draw element index
                        draw.text((x1, y1-25), str(i), fill="red", font=font)
                        
                        # Draw element text if available
                        if "text" in element and element["text"]:
                            text = element["text"][:15] + "..." if len(element["text"]) > 15 else element["text"]
                            draw.text((x1, y1-5), text, fill="blue", font=font)
            
            return np.array(img)
            
        except Exception as e:
            self.logger.error(f"Failed to annotate screenshot: {e}")
            return pixels
    
    def record_agent_action(self, agent_name: str, action: Dict[str, Any], 
                          result: Dict[str, Any]):
        """Record an agent action and its result."""
        if not self.current_trace:
            return
            
        action_record = {
            "timestamp": time.time(),
            "agent": agent_name,
            "action": action,
            "result": result,
            "frame_id": self.current_trace["metadata"]["frame_count"]
        }
        
        self.current_trace["agent_actions"].append(action_record)
    
    def record_ui_state(self, ui_state: Dict[str, Any]):
        """Record current UI state."""
        if not self.current_trace:
            return
            
        ui_record = {
            "timestamp": time.time(),
            "ui_elements": ui_state.get("ui_elements", []),
            "screen_info": ui_state.get("screen_info", {}),
            "frame_id": self.current_trace["metadata"]["frame_count"]
        }
        
        self.current_trace["ui_states"].append(ui_record)
    
    def end_trace(self) -> Optional[str]:
        """End current trace and save metadata."""
        if not self.current_trace:
            return None
            
        self.current_trace["end_time"] = time.time()
        self.current_trace["metadata"]["total_duration"] = (
            self.current_trace["end_time"] - self.current_trace["start_time"]
        )
        
        # Save trace metadata
        trace_path = self.current_trace["metadata"]["trace_path"]
        metadata_path = os.path.join(trace_path, "trace_metadata.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(self.current_trace, f, indent=2, default=str)
        
        trace_id = self.trace_id
        self.current_trace = None
        self.trace_id = None
        
        self.logger.info(f"Ended visual trace recording: {trace_id}")
        return trace_id

class MockLLMProcessor:
    """
    Mock LLM processor that simulates Gemini 2.5 Flash for analyzing traces.
    Provides realistic AI-powered analysis without requiring actual API calls.
    """
    
    def __init__(self):
        self.model_name = "gemini-2.5-flash-mock"
        self.logger = logging.getLogger("MockLLMProcessor")
    
    def analyze_test_trace(self, trace_data: Dict[str, Any], 
                          agent_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze complete test trace and provide AI-powered insights.
        
        Args:
            trace_data: Visual trace data with screenshots and UI states
            agent_logs: Agent decision logs from all agents
            
        Returns:
            Analysis with prompt improvements, failure detection, and recommendations
        """
        
        # Simulate processing time
        time.sleep(0.5)
        
        analysis_start = time.time()
        
        # Analyze trace characteristics
        frame_count = len(trace_data.get("frames", []))
        action_count = len(trace_data.get("agent_actions", []))
        duration = trace_data.get("metadata", {}).get("total_duration", 0)
        
        # Simulate AI analysis based on trace patterns
        analysis_result = {
            "analysis_id": f"analysis_{int(time.time())}",
            "model_used": self.model_name,
            "timestamp": datetime.now().isoformat(),
            "trace_summary": {
                "total_frames": frame_count,
                "total_actions": action_count,
                "duration_seconds": duration,
                "actions_per_minute": (action_count / (duration / 60)) if duration > 0 else 0
            },
            "prompt_improvements": self._suggest_prompt_improvements(trace_data, agent_logs),
            "failure_analysis": self._analyze_failures(trace_data, agent_logs),
            "test_coverage": self._analyze_test_coverage(trace_data, agent_logs),
            "agent_performance": self._analyze_agent_performance(agent_logs),
            "recommendations": self._generate_recommendations(trace_data, agent_logs),
            "processing_time": time.time() - analysis_start
        }
        
        return analysis_result
    
    def _suggest_prompt_improvements(self, trace_data: Dict, agent_logs: List[Dict]) -> List[Dict[str, Any]]:
        """Suggest improvements to agent prompts based on observed behavior."""
        improvements = []
        
        # Analyze planner effectiveness
        planner_logs = [log for log in agent_logs if log.get("agent") == "PlannerAgent"]
        if planner_logs:
            replanning_count = sum(1 for log in planner_logs if "replanning" in log.get("action", ""))
            if replanning_count > 2:
                improvements.append({
                    "agent": "PlannerAgent",
                    "issue": "Excessive replanning detected",
                    "suggestion": "Improve initial planning by adding more comprehensive modal state analysis",
                    "impact": "high",
                    "evidence": f"{replanning_count} replanning events observed"
                })
        
        # Analyze executor effectiveness
        executor_logs = [log for log in agent_logs if log.get("agent") == "ExecutorAgent"]
        failed_actions = [log for log in executor_logs if log.get("status") == "failed"]
        if len(failed_actions) > 1:
            improvements.append({
                "agent": "ExecutorAgent",
                "issue": "Multiple action failures detected",
                "suggestion": "Add more robust element detection and retry strategies",
                "impact": "medium",
                "evidence": f"{len(failed_actions)} failed actions out of {len(executor_logs)} total"
            })
        
        # Analyze verifier effectiveness
        verifier_logs = [log for log in agent_logs if log.get("agent") == "VerifierAgent"]
        if verifier_logs:
            false_positives = [log for log in verifier_logs 
                             if log.get("verification_result", {}).get("status") == "FAIL" 
                             and "false_positive" in str(log)]
            if false_positives:
                improvements.append({
                    "agent": "VerifierAgent",
                    "issue": "Potential false positive bug detections",
                    "suggestion": "Refine bug detection heuristics to reduce false positives",
                    "impact": "medium",
                    "evidence": f"{len(false_positives)} potential false positives"
                })
        
        return improvements
    
    def _analyze_failures(self, trace_data: Dict, agent_logs: List[Dict]) -> Dict[str, Any]:
        """Analyze failures and their root causes."""
        
        failures = []
        
        # Check for UI element detection failures
        ui_failures = 0
        for action in trace_data.get("agent_actions", []):
            if "element_not_found" in str(action.get("result", {})):
                ui_failures += 1
                failures.append({
                    "type": "element_detection_failure",
                    "timestamp": action.get("timestamp"),
                    "agent": action.get("agent"),
                    "details": "UI element could not be located"
                })
        
        # Check for timeout failures
        timeout_failures = [log for log in agent_logs if "timeout" in str(log).lower()]
        for failure in timeout_failures:
            failures.append({
                "type": "timeout_failure",
                "timestamp": failure.get("timestamp"),
                "agent": failure.get("agent"),
                "details": "Operation timed out"
            })
        
        # Check for modal blocking issues
        modal_blocks = [log for log in agent_logs if "blocking_modal" in str(log)]
        for block in modal_blocks:
            failures.append({
                "type": "modal_blocking",
                "timestamp": block.get("timestamp"),
                "agent": block.get("agent"),
                "details": "Unexpected modal blocked execution"
            })
        
        return {
            "total_failures": len(failures),
            "failure_types": {
                "ui_detection": ui_failures,
                "timeouts": len(timeout_failures),
                "modal_blocking": len(modal_blocks)
            },
            "failure_details": failures,
            "failure_rate": len(failures) / max(len(agent_logs), 1)
        }
    
    def _analyze_test_coverage(self, trace_data: Dict, agent_logs: List[Dict]) -> Dict[str, Any]:
        """Analyze test coverage and suggest expansions."""
        
        # Analyze actions performed
        actions_performed = set()
        for action in trace_data.get("agent_actions", []):
            # Handle both string and dict action formats
            if isinstance(action.get("action"), dict):
                action_type = action.get("action", {}).get("action", "unknown")
            else:
                action_type = action.get("action", "unknown")
            actions_performed.add(action_type)
        
        # Standard mobile testing actions
        expected_actions = {
            "tap", "swipe", "toggle", "navigate", "verify", "type", "long_press"
        }
        
        missing_actions = expected_actions - actions_performed
        
        # Analyze UI coverage
        ui_elements_tested = set()
        for action in trace_data.get("agent_actions", []):
            # Handle both string and dict formats for target
            if isinstance(action.get("action"), dict):
                target = action.get("action", {}).get("target")
            else:
                target = action.get("target")
            if target:
                ui_elements_tested.add(target)
        
        return {
            "actions_covered": list(actions_performed),
            "actions_missing": list(missing_actions),
            "coverage_percentage": (len(actions_performed) / len(expected_actions)) * 100,
            "ui_elements_tested": len(ui_elements_tested),
            "recommendations": [
                f"Add test cases for {action} actions" for action in missing_actions
            ]
        }
    
    def _analyze_agent_performance(self, agent_logs: List[Dict]) -> Dict[str, Any]:
        """Analyze individual agent performance metrics."""
        
        performance = {}
        
        for agent_type in ["PlannerAgent", "ExecutorAgent", "VerifierAgent"]:
            agent_actions = [log for log in agent_logs if log.get("agent") == agent_type]
            
            if agent_actions:
                # Calculate success rate
                successful_actions = [log for log in agent_actions 
                                    if log.get("status") != "failed"]
                success_rate = len(successful_actions) / len(agent_actions)
                
                # Calculate average processing time
                processing_times = [log.get("processing_time", 0) for log in agent_actions 
                                  if log.get("processing_time")]
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
                
                performance[agent_type] = {
                    "total_actions": len(agent_actions),
                    "success_rate": success_rate,
                    "avg_processing_time": avg_processing_time,
                    "performance_score": success_rate * (1 / max(avg_processing_time, 0.1))
                }
        
        return performance
    
    def _generate_recommendations(self, trace_data: Dict, agent_logs: List[Dict]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations for improvement."""
        
        recommendations = []
        
        # Performance recommendations
        duration = trace_data.get("metadata", {}).get("total_duration", 0)
        if duration > 60:  # Test took over 1 minute
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "title": "Optimize test execution time",
                "description": f"Test duration of {duration:.1f}s is longer than optimal",
                "actions": [
                    "Reduce wait times between actions",
                    "Implement more efficient element detection",
                    "Parallelize independent verification steps"
                ]
            })
        
        # Reliability recommendations
        failed_actions = [log for log in agent_logs if log.get("status") == "failed"]
        if len(failed_actions) > 2:
            recommendations.append({
                "category": "reliability",
                "priority": "high",
                "title": "Improve action reliability",
                "description": f"{len(failed_actions)} failed actions detected",
                "actions": [
                    "Add more robust element selectors",
                    "Implement better retry mechanisms",
                    "Improve error handling and recovery"
                ]
            })
        
        # Coverage recommendations
        action_count = len(trace_data.get("agent_actions", []))
        if action_count < 5:
            recommendations.append({
                "category": "coverage",
                "priority": "medium",
                "title": "Expand test coverage",
                "description": f"Only {action_count} actions performed",
                "actions": [
                    "Add more comprehensive test scenarios",
                    "Test edge cases and error conditions",
                    "Include negative testing scenarios"
                ]
            })
        
        return recommendations

class SupervisorAgent:
    """
    Enhanced Supervisor Agent that processes full test traces, provides AI-powered analysis,
    and generates comprehensive evaluation reports.
    """
    
    def __init__(self, enable_visual_traces: bool = True, 
                 enable_ai_analysis: bool = True):
        self.enable_visual_traces = enable_visual_traces
        self.enable_ai_analysis = enable_ai_analysis
        self.logger = logging.getLogger("SupervisorAgent")
        
        # Initialize components
        if enable_visual_traces:
            self.trace_recorder = VisualTraceRecorder()
        else:
            self.trace_recorder = None
            
        if enable_ai_analysis:
            self.llm_processor = MockLLMProcessor()
        else:
            self.llm_processor = None
        
        # Tracking
        self.current_session_id = None
        self.agent_logs = []
        
    def start_supervision_session(self, test_goal: str, task_name: str) -> str:
        """Start a new supervision session."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_name}"
        self.current_session_id = session_id
        self.agent_logs = []
        
        # Start visual trace recording
        if self.trace_recorder:
            self.trace_recorder.start_trace(test_goal, task_name)
        
        self.logger.info(f"Started supervision session: {session_id}")
        return session_id
    
    def record_agent_decision(self, agent_name: str, decision_data: Dict[str, Any]):
        """Record agent decision for later analysis."""
        log_entry = {
            "timestamp": time.time(),
            "agent": agent_name,
            "session_id": self.current_session_id,
            **decision_data
        }
        self.agent_logs.append(log_entry)
    
    def capture_environment_state(self, env_state: Dict[str, Any], 
                                 agent_action: Optional[Dict[str, Any]] = None,
                                 action_result: Optional[Dict[str, Any]] = None):
        """Capture current environment state and render visual trace."""
        if not self.trace_recorder:
            return None
            
        # Render current state
        frame_path = self.trace_recorder.render(env_state, mode='save')
        
        # Record UI state
        self.trace_recorder.record_ui_state(env_state)
        
        # Record agent action if provided
        if agent_action and action_result:
            agent_name = agent_action.get("agent", "unknown")
            self.trace_recorder.record_agent_action(agent_name, agent_action, action_result)
        
        return frame_path
    
    def generate_comprehensive_evaluation(self, test_goal: str, 
                                        final_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report with AI analysis.
        """
        evaluation_start = time.time()
        
        # End visual trace recording
        trace_data = None
        if self.trace_recorder:
            trace_id = self.trace_recorder.end_trace()
            trace_data = self.trace_recorder.current_trace
        
        # Perform AI analysis
        ai_analysis = None
        if self.llm_processor and trace_data:
            ai_analysis = self.llm_processor.analyze_test_trace(trace_data, self.agent_logs)
        
        # Generate evaluation report
        overall_status = "PASS" if all(r.get("result") == "PASS" for r in final_results) else "FAIL"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        evaluation_report = {
            "evaluation_id": f"eval_{timestamp}",
            "session_id": self.current_session_id,
            "test_goal": test_goal,
            "overall_status": overall_status,
            "timestamp": timestamp,
            "processing_time": time.time() - evaluation_start,
            
            # Core results
            "test_results": final_results,
            "agent_decision_logs": self.agent_logs,
            
            # Visual trace data
            "visual_trace": {
                "enabled": self.enable_visual_traces,
                "trace_id": trace_data.get("trace_id") if trace_data else None,
                "frame_count": len(trace_data.get("frames", [])) if trace_data else 0,
                "trace_duration": trace_data.get("metadata", {}).get("total_duration", 0) if trace_data else 0
            },
            
            # AI Analysis
            "ai_analysis": ai_analysis,
            
            # Performance metrics
            "metrics": self._calculate_performance_metrics(final_results, trace_data),
            
            # Summary statistics
            "statistics": self._generate_statistics(final_results, trace_data, self.agent_logs)
        }
        
        # Save comprehensive report
        self._save_comprehensive_report(evaluation_report)
        
        return evaluation_report
    
    def _calculate_performance_metrics(self, results: List[Dict], 
                                     trace_data: Optional[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics."""
        
        metrics = {
            "bug_detection_accuracy": self._calculate_bug_detection_accuracy(results),
            "agent_recovery_ability": self._calculate_recovery_ability(),
            "test_efficiency": self._calculate_test_efficiency(trace_data),
            "coverage_completeness": self._calculate_coverage_completeness(results)
        }
        
        return metrics
    
    def _calculate_bug_detection_accuracy(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate bug detection accuracy metrics."""
        
        # Count true positives, false positives, false negatives
        verifier_logs = [log for log in self.agent_logs if log.get("agent") == "VerifierAgent"]
        
        bugs_detected = 0
        false_positives = 0
        true_positives = 0
        
        for log in verifier_logs:
            verification_result = log.get("verification_result", {})
            functional_bugs = verification_result.get("functional_bugs", [])
            
            bugs_detected += len(functional_bugs)
            
            # Simulate accuracy assessment (in real implementation, 
            # this would compare against known ground truth)
            for bug in functional_bugs:
                confidence = bug.get("confidence", 0.5)
                if confidence > 0.8:
                    true_positives += 1
                elif confidence < 0.3:
                    false_positives += 1
        
        precision = true_positives / max(bugs_detected, 1)
        recall = true_positives / max(true_positives + 1, 1)  # Assuming 1 known bug
        f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
        
        return {
            "bugs_detected": bugs_detected,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }
    
    def _calculate_recovery_ability(self) -> Dict[str, Any]:
        """Calculate agent recovery ability metrics."""
        
        # Find replanning events
        replanning_logs = [log for log in self.agent_logs 
                          if "replanning" in log.get("action", "")]
        
        # Find error recovery events
        recovery_logs = [log for log in self.agent_logs 
                        if "recovery" in str(log) or "retry" in str(log)]
        
        # Calculate success rate of recovery attempts
        successful_recoveries = [log for log in recovery_logs 
                                if log.get("status") == "success"]
        
        recovery_success_rate = (len(successful_recoveries) / 
                               max(len(recovery_logs), 1))
        
        return {
            "replanning_events": len(replanning_logs),
            "recovery_attempts": len(recovery_logs),
            "successful_recoveries": len(successful_recoveries),
            "recovery_success_rate": recovery_success_rate,
            "adaptation_score": min(recovery_success_rate * 1.2, 1.0)
        }
    
    def _calculate_test_efficiency(self, trace_data: Optional[Dict]) -> Dict[str, Any]:
        """Calculate test execution efficiency metrics."""
        
        if not trace_data:
            return {"efficiency_score": 0.5, "details": "No trace data available"}
        
        duration = trace_data.get("metadata", {}).get("total_duration", 0)
        frame_count = len(trace_data.get("frames", []))
        action_count = len(trace_data.get("agent_actions", []))
        
        # Calculate efficiency metrics
        actions_per_second = action_count / max(duration, 1)
        frames_per_action = frame_count / max(action_count, 1)
        
        # Efficiency score (higher is better, normalized to 0-1)
        efficiency_score = min(actions_per_second * 0.3, 1.0)
        
        return {
            "duration_seconds": duration,
            "actions_per_second": actions_per_second,
            "frames_per_action": frames_per_action,
            "efficiency_score": efficiency_score
        }
    
    def _calculate_coverage_completeness(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate test coverage completeness."""
        
        # Analyze what was tested vs what should be tested
        tested_features = set()
        for result in results:
            step_description = result.get("step", "")
            if "wifi" in step_description.lower():
                tested_features.add("wifi_functionality")
            if "toggle" in step_description.lower():
                tested_features.add("toggle_operations")
            if "navigation" in step_description.lower():
                tested_features.add("app_navigation")
        
        # Expected features for comprehensive testing
        expected_features = {
            "wifi_functionality", "toggle_operations", "app_navigation",
            "error_handling", "state_persistence", "ui_responsiveness"
        }
        
        coverage_percentage = (len(tested_features) / len(expected_features)) * 100
        
        return {
            "tested_features": list(tested_features),
            "expected_features": list(expected_features),
            "coverage_percentage": coverage_percentage,
            "missing_features": list(expected_features - tested_features)
        }
    
    def _generate_statistics(self, results: List[Dict], 
                           trace_data: Optional[Dict],
                           agent_logs: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics."""
        
        return {
            "total_test_steps": len(results),
            "passed_steps": len([r for r in results if r.get("result") == "PASS"]),
            "failed_steps": len([r for r in results if r.get("result") == "FAIL"]),
            "total_agent_decisions": len(agent_logs),
            "unique_agents": len(set(log.get("agent") for log in agent_logs)),
            "visual_frames_captured": len(trace_data.get("frames", [])) if trace_data else 0,
            "test_success_rate": (len([r for r in results if r.get("result") == "PASS"]) / 
                                max(len(results), 1)) * 100
        }
    
    def _save_comprehensive_report(self, evaluation_report: Dict[str, Any]):
        """Save comprehensive evaluation report in multiple formats."""
        
        timestamp = evaluation_report["timestamp"]
        
        # Ensure reports directory exists
        os.makedirs("reports", exist_ok=True)
        
        # Save detailed JSON report
        json_path = f"reports/supervisor_evaluation_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(evaluation_report, f, indent=2, default=str)
        
        # Generate executive summary markdown
        md_path = f"reports/supervisor_summary_{timestamp}.md"
        self._generate_executive_summary_markdown(evaluation_report, md_path)
        
        # Generate HTML report if trace data exists
        if evaluation_report["visual_trace"]["enabled"]:
            html_path = f"reports/visual_report_{timestamp}.html"
            self._generate_visual_html_report(evaluation_report, html_path)
        
        print(f"\n[Supervisor Agent] Comprehensive evaluation completed:")
        print(f"- Detailed JSON: {json_path}")
        print(f"- Executive Summary: {md_path}")
        if evaluation_report["visual_trace"]["enabled"]:
            print(f"- Visual Report: {html_path}")
        print(f"Overall Result: {evaluation_report['overall_status']}")
        
        # Print key insights
        if evaluation_report.get("ai_analysis"):
            self._print_key_insights(evaluation_report["ai_analysis"])
    
    def _generate_executive_summary_markdown(self, report: Dict[str, Any], 
                                           output_path: str):
        """Generate executive summary in markdown format."""
        
        ai_analysis = report.get("ai_analysis", {})
        metrics = report.get("metrics", {})
        
        md_content = f"""# QA Test Evaluation Report
        
## Executive Summary
**Test Goal:** {report['test_goal']}  
**Overall Result:** {report['overall_status']}  
**Test Date:** {report['timestamp']}  
**Session ID:** {report['session_id']}

## Key Metrics
- **Bug Detection Accuracy:** {metrics.get('bug_detection_accuracy', {}).get('f1_score', 0):.2f} F1-Score
- **Agent Recovery Ability:** {metrics.get('agent_recovery_ability', {}).get('recovery_success_rate', 0):.2f} Success Rate
- **Test Efficiency:** {metrics.get('test_efficiency', {}).get('efficiency_score', 0):.2f}/1.0
- **Coverage Completeness:** {metrics.get('coverage_completeness', {}).get('coverage_percentage', 0):.1f}%

## Visual Trace Summary
- **Frames Captured:** {report['visual_trace']['frame_count']}
- **Trace Duration:** {report['visual_trace']['trace_duration']:.1f} seconds
- **Trace ID:** {report['visual_trace']['trace_id']}

## AI Analysis Insights
"""
        
        if ai_analysis:
            # Add prompt improvements
            improvements = ai_analysis.get("prompt_improvements", [])
            if improvements:
                md_content += "\n### Prompt Improvement Suggestions\n"
                for imp in improvements:
                    md_content += f"- **{imp['agent']}:** {imp['suggestion']} ({imp['impact']} impact)\n"
            
            # Add failure analysis
            failure_analysis = ai_analysis.get("failure_analysis", {})
            if failure_analysis:
                md_content += f"\n### Failure Analysis\n"
                md_content += f"- **Total Failures:** {failure_analysis.get('total_failures', 0)}\n"
                md_content += f"- **Failure Rate:** {failure_analysis.get('failure_rate', 0):.2%}\n"
            
            # Add recommendations
            recommendations = ai_analysis.get("recommendations", [])
            if recommendations:
                md_content += "\n### Recommendations\n"
                for rec in recommendations:
                    md_content += f"- **{rec['title']}** ({rec['priority']} priority): {rec['description']}\n"
        
        # Add test step results
        md_content += "\n## Test Step Results\n"
        for i, result in enumerate(report['test_results'], 1):
            status_emoji = "✅" if result.get("result") == "PASS" else "❌"
            md_content += f"{i}. {status_emoji} {result.get('step', 'Unknown step')}\n"
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _generate_visual_html_report(self, report: Dict[str, Any], 
                                   output_path: str):
        """Generate visual HTML report with embedded screenshots."""
        
        # This is a simplified version - in practice, you'd embed actual screenshots
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>QA Visual Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e8f4fd; border-radius: 3px; }}
        .frame {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
        .status-pass {{ color: green; font-weight: bold; }}
        .status-fail {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>QA Visual Test Report</h1>
        <p><strong>Test Goal:</strong> {report['test_goal']}</p>
        <p><strong>Overall Result:</strong> 
           <span class="status-{report['overall_status'].lower()}">{report['overall_status']}</span></p>
        <p><strong>Session ID:</strong> {report['session_id']}</p>
    </div>
    
    <h2>Performance Metrics</h2>
    <div class="metrics">
"""
        
        metrics = report.get("metrics", {})
        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict):
                score = metric_data.get("f1_score") or metric_data.get("efficiency_score") or metric_data.get("coverage_percentage", 0)
                html_content += f'<div class="metric">{metric_name.replace("_", " ").title()}: {score:.2f}</div>'
        
        html_content += """
    </div>
    
    <h2>Visual Trace</h2>
    <p>Screenshots and UI states captured during test execution would be displayed here.</p>
    
    <h2>Test Steps</h2>
"""
        
        for i, result in enumerate(report['test_results'], 1):
            status_class = "status-pass" if result.get("result") == "PASS" else "status-fail"
            html_content += f'<div class="frame">{i}. <span class="{status_class}">{result.get("result")}</span> - {result.get("step", "Unknown")}</div>'
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _print_key_insights(self, ai_analysis: Dict[str, Any]):
        """Print key insights from AI analysis."""
        
        print("\n🔍 AI Analysis Key Insights:")
        
        # Print prompt improvements
        improvements = ai_analysis.get("prompt_improvements", [])
        if improvements:
            print(f"📝 {len(improvements)} prompt improvements suggested")
            for imp in improvements[:2]:  # Show top 2
                print(f"   • {imp['agent']}: {imp['suggestion']}")
        
        # Print failure analysis
        failure_analysis = ai_analysis.get("failure_analysis", {})
        if failure_analysis:
            total_failures = failure_analysis.get("total_failures", 0)
            if total_failures > 0:
                print(f"⚠️  {total_failures} failures detected and analyzed")
        
        # Print top recommendation
        recommendations = ai_analysis.get("recommendations", [])
        if recommendations:
            top_rec = recommendations[0]
            print(f"💡 Top recommendation: {top_rec['title']} ({top_rec['priority']} priority)")

# Legacy function for backward compatibility
def summarize_results(test_goal, results):
    """Legacy function - use SupervisorAgent for enhanced functionality."""
    supervisor = SupervisorAgent(enable_visual_traces=False, enable_ai_analysis=False)
    
    # Calculate overall status
    overall_status = "PASS" if all(r.get("result") == "PASS" for r in results) else "FAIL"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Ensure reports folder exists
    os.makedirs("reports", exist_ok=True)

    # JSON report
    json_report = {
        "test_goal": test_goal,
        "overall_status": overall_status,
        "steps": results,
        "timestamp": timestamp
    }
    json_path = f"reports/qa_report_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=4)

    # Markdown report
    md_lines = [f"# QA Test Report", f"**Test Goal:** {test_goal}", f"**Overall Result:** {overall_status}", "", "## Step Results:"]
    for i, r in enumerate(results, start=1):
        md_lines.append(f"- Step {i}: {r['step']} → **{r['result']}**")
    md_content = "\n".join(md_lines)

    md_path = f"reports/qa_report_{timestamp}.md"
    with open(md_path, "w") as f:
        f.write(md_content)

    print(f"\n[Supervisor Agent] Report generated:")
    print(f"- JSON: {json_path}")
    print(f"- Markdown: {md_path}")
    print(f"Overall Test Result: {overall_status}")

    return overall_status
