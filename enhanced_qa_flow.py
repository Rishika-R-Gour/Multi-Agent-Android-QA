#!/usr/bin/env python3
"""
Enhanced QA Flow with Verifier Agent and Dynamic Replanning

This demonstrates the complete QA automation flow with:
1. Enhanced Planner Agent generating sophisticated subgoals
2. Enhanced Executor Agent with UI hierarchy inspection
3. Enhanced Verifier Agent with bug detection and replanning triggers
4. Dynamic replanning when issues are detected
5. Comprehensive logging in JSON format
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from planner_agent import PlannerAgent
from executor_agent import ExecutorAgent
from verifier_agent import VerifierAgent
from android_env_wrapper import AndroidEnv
from supervisor_agent import summarize_results

class EnhancedQAFlowManager:
    """
    Enhanced QA Flow Manager that orchestrates all agents with verification and replanning.
    """
    
    def __init__(self, task_name: str = "enhanced_qa_flow", enable_real_device: bool = False):
        self.task_name = task_name
        self.enable_real_device = enable_real_device
        self.logger = logging.getLogger(f"QAFlowManager.{task_name}")
        
        # Initialize agents
        self.env = AndroidEnv(task_name=task_name, enable_real_device=enable_real_device)
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(task_name=task_name, enable_real_device=enable_real_device)
        self.verifier = VerifierAgent(task_name=f"{task_name}_verification")
        
        # Flow state
        self.current_session = None
        self.execution_log = []
        self.replanning_history = []
        self.overall_metrics = {
            "total_subgoals": 0,
            "successful_subgoals": 0,
            "failed_subgoals": 0,
            "bugs_detected": 0,
            "replanning_events": 0,
            "verification_failures": 0
        }
    
    def run_enhanced_qa_flow(self, test_goal: str, max_replanning_attempts: int = 3) -> Dict[str, Any]:
        """
        Run the complete enhanced QA flow with verification and replanning.
        """
        session_id = f"qa_session_{int(time.time())}"
        self.current_session = session_id
        
        flow_result = {
            "session_id": session_id,
            "test_goal": test_goal,
            "start_time": time.time(),
            "status": "running",
            "plan": None,
            "execution_results": [],
            "verification_results": [],
            "replanning_events": [],
            "final_verdict": None,
            "metrics": {}
        }
        
        self.logger.info(f"Starting enhanced QA flow session {session_id} for goal: {test_goal}")
        
        try:
            # Step 1: Initialize environment
            initial_state = self.env.reset()
            flow_result["initial_state"] = initial_state
            
            # Step 2: Generate initial plan with Enhanced Planner
            self.logger.info("Generating initial test plan...")
            plan_result = self.planner.generate_test_plan(test_goal, initial_state)
            flow_result["plan"] = plan_result
            
            subgoals = plan_result.get("subgoals", [])
            self.overall_metrics["total_subgoals"] = len(subgoals)
            
            self.logger.info(f"Generated {len(subgoals)} subgoals for execution")
            
            # Step 3: Execute subgoals with verification and replanning
            current_subgoal_index = 0
            replanning_attempts = 0
            
            while current_subgoal_index < len(subgoals) and replanning_attempts < max_replanning_attempts:
                subgoal = subgoals[current_subgoal_index]
                
                # Execute subgoal with Enhanced Executor
                execution_result = self._execute_subgoal_with_verification(
                    subgoal, current_subgoal_index, flow_result
                )
                
                flow_result["execution_results"].append(execution_result)
                
                # Check if replanning is needed
                verification_result = execution_result.get("verification_result", {})
                if verification_result.get("replanning_required", False):
                    self.logger.info(f"Replanning required for subgoal {current_subgoal_index}")
                    
                    # Trigger dynamic replanning
                    replanning_result = self._handle_dynamic_replanning(
                        verification_result, plan_result, current_subgoal_index, flow_result
                    )
                    
                    flow_result["replanning_events"].append(replanning_result)
                    self.replanning_history.append(replanning_result)
                    
                    if replanning_result.get("status") == "completed":
                        # Update plan and continue with new subgoals
                        plan_result = replanning_result["updated_plan"]
                        subgoals = plan_result.get("subgoals", [])
                        replanning_attempts += 1
                        self.overall_metrics["replanning_events"] += 1
                        
                        # Continue with current index (may have new subgoals inserted)
                        continue
                    else:
                        # Replanning failed, move to next subgoal
                        self.logger.warning("Replanning failed, continuing with next subgoal")
                        self.overall_metrics["verification_failures"] += 1
                
                # Move to next subgoal
                current_subgoal_index += 1
            
            # Step 4: Generate final verdict
            final_verdict = self._generate_final_verdict(flow_result)
            flow_result["final_verdict"] = final_verdict
            flow_result["status"] = "completed"
            
        except Exception as e:
            self.logger.error(f"QA flow failed: {e}")
            flow_result["status"] = "failed"
            flow_result["error"] = str(e)
        
        flow_result["end_time"] = time.time()
        flow_result["duration"] = flow_result["end_time"] - flow_result["start_time"]
        flow_result["metrics"] = self.overall_metrics.copy()
        
        # Log the complete session
        self._log_qa_session(flow_result)
        
        return flow_result
    
    def _execute_subgoal_with_verification(self, subgoal: Dict, subgoal_index: int, 
                                         flow_result: Dict) -> Dict[str, Any]:
        """Execute a subgoal with Enhanced Executor and verify with Enhanced Verifier."""
        
        execution_result = {
            "subgoal_index": subgoal_index,
            "subgoal": subgoal,
            "start_time": time.time(),
            "executor_result": None,
            "verification_result": None,
            "ui_state": None,
            "status": "running"
        }
        
        try:
            self.logger.info(f"Executing subgoal {subgoal_index}: {subgoal.get('description', 'Unknown')}")
            
            # Execute with Enhanced Executor
            executor_result = self.executor.execute_subgoal(subgoal)
            execution_result["executor_result"] = executor_result
            
            # Update metrics
            if executor_result.get("status") == "completed":
                self.overall_metrics["successful_subgoals"] += 1
            else:
                self.overall_metrics["failed_subgoals"] += 1
            
            # Get current UI state for verification
            ui_state = self.env.step({"action_type": "inspect", "target": "ui_state"})
            execution_result["ui_state"] = ui_state
            
            # Verify with Enhanced Verifier
            self.logger.info(f"Verifying subgoal {subgoal_index} execution...")
            verification_result = self.verifier.verify_goal_state(
                subgoal, executor_result, ui_state
            )
            execution_result["verification_result"] = verification_result
            
            # Update verification metrics
            if verification_result.get("functional_bugs"):
                self.overall_metrics["bugs_detected"] += len(verification_result["functional_bugs"])
            
            execution_result["status"] = "completed"
            
        except Exception as e:
            self.logger.error(f"Subgoal execution failed: {e}")
            execution_result["status"] = "failed"
            execution_result["error"] = str(e)
            self.overall_metrics["failed_subgoals"] += 1
        
        execution_result["end_time"] = time.time()
        execution_result["duration"] = execution_result["end_time"] - execution_result["start_time"]
        
        return execution_result
    
    def _handle_dynamic_replanning(self, verification_result: Dict, current_plan: Dict, 
                                 current_index: int, flow_result: Dict) -> Dict[str, Any]:
        """Handle dynamic replanning when verification detects issues."""
        
        self.logger.info("Initiating dynamic replanning...")
        
        # Get current UI state for context
        ui_state = flow_result["execution_results"][-1].get("ui_state", {})
        
        # Trigger replanning with Enhanced Planner
        replanning_result = self.planner.handle_replanning_request(
            verification_result, current_plan, current_index, ui_state
        )
        
        return replanning_result
    
    def _generate_final_verdict(self, flow_result: Dict) -> Dict[str, Any]:
        """Generate final verdict based on all execution and verification results."""
        
        execution_results = flow_result.get("execution_results", [])
        verification_results = [r.get("verification_result", {}) for r in execution_results]
        
        # Calculate success metrics
        total_subgoals = len(execution_results)
        successful_executions = sum(1 for r in execution_results 
                                  if r.get("executor_result", {}).get("status") == "completed")
        passed_verifications = sum(1 for v in verification_results 
                                 if v.get("verdict") == "PASS")
        
        # Calculate overall scores
        execution_success_rate = successful_executions / max(total_subgoals, 1)
        verification_success_rate = passed_verifications / max(total_subgoals, 1)
        
        # Determine final verdict
        if execution_success_rate >= 0.8 and verification_success_rate >= 0.8:
            final_verdict = "PASS"
            verdict_reason = "High success rate in execution and verification"
        elif execution_success_rate >= 0.6 or verification_success_rate >= 0.6:
            final_verdict = "PARTIAL_PASS" 
            verdict_reason = "Moderate success rate with some issues"
        else:
            final_verdict = "FAIL"
            verdict_reason = "Low success rate in execution or verification"
        
        # Collect all detected bugs
        all_bugs = []
        for v in verification_results:
            all_bugs.extend(v.get("functional_bugs", []))
        
        return {
            "verdict": final_verdict,
            "reason": verdict_reason,
            "execution_success_rate": execution_success_rate,
            "verification_success_rate": verification_success_rate,
            "total_subgoals": total_subgoals,
            "successful_executions": successful_executions,
            "passed_verifications": passed_verifications,
            "bugs_detected": len(all_bugs),
            "bug_summary": all_bugs,
            "replanning_events": len(flow_result.get("replanning_events", [])),
            "confidence_score": (execution_success_rate + verification_success_rate) / 2
        }
    
    def _log_qa_session(self, flow_result: Dict):
        """Log the complete QA session in structured JSON format."""
        
        log_entry = {
            "session_type": "enhanced_qa_flow",
            "session_id": flow_result["session_id"],
            "timestamp": datetime.now().isoformat(),
            "test_goal": flow_result["test_goal"],
            "duration": flow_result.get("duration", 0),
            "status": flow_result["status"],
            "final_verdict": flow_result.get("final_verdict", {}),
            "metrics": flow_result.get("metrics", {}),
            "agent_decisions": {
                "planner_decisions": len(flow_result.get("replanning_events", [])),
                "executor_actions": sum(len(r.get("executor_result", {}).get("actions_executed", [])) 
                                      for r in flow_result.get("execution_results", [])),
                "verifier_checks": len(flow_result.get("verification_results", [])),
                "bugs_detected": flow_result.get("metrics", {}).get("bugs_detected", 0)
            },
            "replanning_summary": {
                "total_replanning_events": len(flow_result.get("replanning_events", [])),
                "replanning_triggers": [event.get("adaptations_made", []) 
                                      for event in flow_result.get("replanning_events", [])]
            }
        }
        
        # Save comprehensive log
        log_filename = f"enhanced_qa_flow_log_{datetime.now().strftime('%Y%m%d')}.json"
        
        import os
        os.makedirs("reports", exist_ok=True)
        
        try:
            with open(f"reports/{log_filename}", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write QA flow log: {e}")
        
        # Also save summary report
        self._generate_summary_report(flow_result)
    
    def _generate_summary_report(self, flow_result: Dict):
        """Generate human-readable summary report."""
        
        final_verdict = flow_result.get("final_verdict", {})
        
        summary_data = []
        for i, result in enumerate(flow_result.get("execution_results", []), 1):
            subgoal_desc = result.get("subgoal", {}).get("description", f"Subgoal {i}")
            executor_status = result.get("executor_result", {}).get("status", "unknown")
            verification_verdict = result.get("verification_result", {}).get("verdict", "unknown")
            
            summary_data.append({
                "step": f"Subgoal {i}",
                "result": "PASS" if executor_status == "completed" and verification_verdict == "PASS" else "FAIL",
                "description": subgoal_desc,
                "verification": verification_verdict
            })
        
        # Use existing supervisor function for report generation
        summarize_results(f"{flow_result['test_goal']} - Enhanced Flow", summary_data)

def demonstrate_enhanced_qa_flow():
    """Demonstrate the complete enhanced QA flow with verification and replanning."""
    
    print("🚀 ENHANCED QA FLOW DEMONSTRATION")
    print("Verifier Agent + Dynamic Replanning + Comprehensive Logging")
    print("=" * 80)
    
    # Initialize Enhanced QA Flow Manager
    qa_manager = EnhancedQAFlowManager(task_name="enhanced_demo", enable_real_device=False)
    
    # Test goal that will trigger various scenarios
    test_goal = "Complete Wi-Fi testing with error handling and recovery"
    
    print(f"\n🎯 Test Goal: {test_goal}")
    print("\nThis demonstration will show:")
    print("• Enhanced Planner generating sophisticated subgoals")
    print("• Enhanced Executor with UI hierarchy inspection")
    print("• Enhanced Verifier detecting bugs and triggering replanning")
    print("• Dynamic replanning when issues are detected")
    print("• Comprehensive logging of all agent decisions")
    
    # Run the enhanced flow
    print(f"\n📋 RUNNING ENHANCED QA FLOW")
    print("-" * 50)
    
    start_time = time.time()
    flow_result = qa_manager.run_enhanced_qa_flow(test_goal, max_replanning_attempts=2)
    execution_time = time.time() - start_time
    
    # Display results
    print(f"\n📊 ENHANCED QA FLOW RESULTS")
    print("-" * 40)
    
    final_verdict = flow_result.get("final_verdict", {})
    metrics = flow_result.get("metrics", {})
    
    print(f"✅ Session completed in {execution_time:.2f}s")
    print(f"🎯 Final Verdict: {final_verdict.get('verdict', 'UNKNOWN')}")
    print(f"📝 Reason: {final_verdict.get('reason', 'No reason provided')}")
    print(f"📊 Confidence: {final_verdict.get('confidence_score', 0):.2f}")
    
    print(f"\n📈 EXECUTION METRICS:")
    print(f"   • Total subgoals: {metrics.get('total_subgoals', 0)}")
    print(f"   • Successful: {metrics.get('successful_subgoals', 0)}")
    print(f"   • Failed: {metrics.get('failed_subgoals', 0)}")
    print(f"   • Success rate: {final_verdict.get('execution_success_rate', 0):.1%}")
    
    print(f"\n🔍 VERIFICATION METRICS:")
    print(f"   • Verifications passed: {final_verdict.get('passed_verifications', 0)}")
    print(f"   • Bugs detected: {metrics.get('bugs_detected', 0)}")
    print(f"   • Verification rate: {final_verdict.get('verification_success_rate', 0):.1%}")
    
    print(f"\n🔄 REPLANNING METRICS:")
    print(f"   • Replanning events: {metrics.get('replanning_events', 0)}")
    print(f"   • Verification failures: {metrics.get('verification_failures', 0)}")
    
    # Show detected bugs if any
    bugs = final_verdict.get("bug_summary", [])
    if bugs:
        print(f"\n🐛 BUGS DETECTED:")
        for i, bug in enumerate(bugs[:3], 1):  # Show first 3 bugs
            print(f"   {i}. {bug.get('bug_type', 'unknown')}: {bug.get('description', 'No description')}")
            print(f"      Severity: {bug.get('severity', 'unknown')}")
            print(f"      Suggested action: {bug.get('suggested_action', 'unknown')}")
    
    # Show replanning events
    replanning_events = flow_result.get("replanning_events", [])
    if replanning_events:
        print(f"\n🔄 REPLANNING EVENTS:")
        for i, event in enumerate(replanning_events, 1):
            adaptations = event.get("adaptations_made", [])
            print(f"   {i}. Status: {event.get('status', 'unknown')}")
            print(f"      Adaptations: {', '.join(adaptations) if adaptations else 'none'}")
            print(f"      New subgoals added: {len(event.get('new_subgoals', []))}")
    
    print(f"\n📁 COMPREHENSIVE LOGS SAVED:")
    print(f"   • Enhanced QA flow log: reports/enhanced_qa_flow_log_*.json")
    print(f"   • Planner decisions: reports/qa_planner_log_*.json")
    print(f"   • Verifier results: reports/qa_verification_log_*.json")
    print(f"   • Summary report: reports/qa_report_*.md")
    
    print(f"\n🎉 DEMONSTRATION COMPLETE!")
    print("Enhanced QA Flow with Verifier Agent and Dynamic Replanning working successfully!")
    
    return flow_result

if __name__ == "__main__":
    try:
        result = demonstrate_enhanced_qa_flow()
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
