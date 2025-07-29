#!/usr/bin/env python3
"""
Enhanced QA Flow integrating Agent-S messaging structure with Android World.
This script demonstrates the complete Setup + Planner + Executor pipeline.
"""

import json
import time
import argparse
from typing import Dict, Any
from planner_agent import PlannerAgent
from executor_agent import ExecutorAgent
from verifier_agent import verify_step
from supervisor_agent import summarize_results
from android_env_wrapper import AndroidEnv

class QAFlowManager:
    """
    Main QA Flow Manager that orchestrates all agents following Agent-S patterns.
    """
    
    def __init__(self, task_name: str = "settings_wifi", enable_real_device: bool = False):
        self.task_name = task_name
        self.enable_real_device = enable_real_device
        
        # Initialize agents
        self.planner = PlannerAgent(task_name)
        self.executor = ExecutorAgent(task_name, enable_real_device)
        
        # Flow state
        self.current_session = {
            "session_id": f"qa_session_{int(time.time())}",
            "task_name": task_name,
            "start_time": time.time(),
            "agents_initialized": True,
            "plans_generated": [],
            "executions_completed": [],
            "overall_status": "initialized"
        }
        
    def run_complete_qa_flow(self, goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the complete QA flow: Planning -> Execution -> Verification -> Reporting
        """
        print(f"\n{'='*60}")
        print(f"🚀 Starting QA Flow for: {goal}")
        print(f"Task: {self.task_name}")
        print(f"Real Device: {self.enable_real_device}")
        print(f"{'='*60}\n")
        
        try:
            # Step 1: Generate Test Plan
            print("📋 Step 1: Generating Test Plan...")
            plan = self.planner.generate_test_plan(goal, context)
            self.current_session["plans_generated"].append(plan)
            
            print(f"✅ Plan generated with {len(plan['steps'])} steps")
            print(f"   Estimated duration: {plan['estimated_duration']} seconds")
            
            # Step 2: Execute Test Plan
            print("\n🔄 Step 2: Executing Test Plan...")
            execution_result = self.executor.execute_plan(plan)
            self.current_session["executions_completed"].append(execution_result)
            
            print(f"✅ Execution completed: {execution_result['overall_status']}")
            print(f"   Duration: {execution_result['duration']:.2f} seconds")
            print(f"   Steps executed: {len(execution_result['steps_executed'])}")
            
            # Step 3: Verify Results
            print("\n🔍 Step 3: Verifying Results...")
            verification_results = self._verify_execution_results(execution_result)
            
            # Step 4: Generate Summary Report
            print("\n📊 Step 4: Generating Summary Report...")
            summary_report = self._generate_qa_report(plan, execution_result, verification_results)
            
            # Update session status
            self.current_session["end_time"] = time.time()
            self.current_session["total_duration"] = (
                self.current_session["end_time"] - self.current_session["start_time"]
            )
            self.current_session["overall_status"] = execution_result["overall_status"]
            self.current_session["summary_report"] = summary_report
            
            print(f"\n🎯 QA Flow Complete!")
            print(f"Overall Status: {self.current_session['overall_status']}")
            print(f"Total Duration: {self.current_session['total_duration']:.2f} seconds")
            
            return self.current_session
            
        except Exception as e:
            print(f"\n❌ QA Flow Failed: {str(e)}")
            self.current_session["overall_status"] = "error"
            self.current_session["error"] = str(e)
            return self.current_session
    
    def _verify_execution_results(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced verification using the verifier agent.
        """
        verification_results = {
            "overall_verification_status": "pending",
            "step_verifications": [],
            "summary": {}
        }
        
        total_steps = len(execution_result["steps_executed"])
        successful_steps = 0
        
        for step_result in execution_result["steps_executed"]:
            # Use legacy verifier for additional verification
            legacy_result = verify_step(step_result["description"])
            
            step_verification = {
                "step_id": step_result["step_id"],
                "execution_status": step_result["status"],
                "validation_results": step_result.get("validation_results", []),
                "legacy_verification": legacy_result,
                "overall_step_status": self._determine_step_verification_status(step_result)
            }
            
            verification_results["step_verifications"].append(step_verification)
            
            if step_verification["overall_step_status"] == "passed":
                successful_steps += 1
        
        # Determine overall verification status
        success_rate = successful_steps / total_steps if total_steps > 0 else 0
        
        if success_rate >= 0.9:
            verification_results["overall_verification_status"] = "passed"
        elif success_rate >= 0.7:
            verification_results["overall_verification_status"] = "partial_pass"
        else:
            verification_results["overall_verification_status"] = "failed"
        
        verification_results["summary"] = {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "success_rate": success_rate,
            "failed_steps": total_steps - successful_steps
        }
        
        return verification_results
    
    def _determine_step_verification_status(self, step_result: Dict[str, Any]) -> str:
        """Determine overall verification status for a single step."""
        if step_result["status"] == "success":
            # Check validation results
            validations = step_result.get("validation_results", [])
            if not validations:
                return "passed"  # No validations to check
            
            failed_validations = [v for v in validations if not v["passed"]]
            if len(failed_validations) == 0:
                return "passed"
            elif len(failed_validations) < len(validations) / 2:
                return "partial_pass"
            else:
                return "failed"
        else:
            return "failed"
    
    def _generate_qa_report(self, plan: Dict, execution_result: Dict, verification_results: Dict) -> Dict[str, Any]:
        """
        Generate comprehensive QA report.
        """
        report = {
            "report_id": f"qa_report_{int(time.time())}",
            "timestamp": time.time(),
            "goal": plan["goal"],
            "task_name": self.task_name,
            "environment": {
                "real_device_used": self.enable_real_device,
                "android_env_status": "active"
            },
            "planning_summary": {
                "plan_id": plan["plan_id"],
                "total_steps_planned": len(plan["steps"]),
                "estimated_duration": plan["estimated_duration"]
            },
            "execution_summary": {
                "actual_duration": execution_result["duration"],
                "steps_executed": len(execution_result["steps_executed"]),
                "overall_status": execution_result["overall_status"]
            },
            "verification_summary": verification_results["summary"],
            "detailed_results": {
                "step_by_step": []
            },
            "recommendations": []
        }
        
        # Add detailed step results
        for i, step_result in enumerate(execution_result["steps_executed"]):
            step_verification = verification_results["step_verifications"][i]
            
            detailed_step = {
                "step_number": step_result["step_id"],
                "description": step_result["description"],
                "execution_status": step_result["status"],
                "execution_duration": step_result["duration"],
                "verification_status": step_verification["overall_step_status"],
                "validation_details": step_result.get("validation_results", []),
                "issues": step_result.get("details", {})
            }
            
            report["detailed_results"]["step_by_step"].append(detailed_step)
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(execution_result, verification_results)
        
        # Use legacy supervisor for additional summary
        legacy_results = []
        for step_result in execution_result["steps_executed"]:
            legacy_results.append({
                "step": step_result["description"],
                "result": step_verification["overall_step_status"]
            })
        
        legacy_summary = summarize_results(plan["goal"], legacy_results)
        report["legacy_summary"] = legacy_summary
        
        return report
    
    def _generate_recommendations(self, execution_result: Dict, verification_results: Dict) -> list:
        """Generate actionable recommendations based on results."""
        recommendations = []
        
        failed_steps = [s for s in execution_result["steps_executed"] if s["status"] != "success"]
        
        if len(failed_steps) > 0:
            recommendations.append({
                "category": "execution_improvements",
                "priority": "high",
                "description": f"{len(failed_steps)} steps failed execution. Review error details and environment setup."
            })
        
        validation_failures = []
        for step_verification in verification_results["step_verifications"]:
            for validation in step_verification.get("validation_results", []):
                if not validation["passed"]:
                    validation_failures.append(validation)
        
        if len(validation_failures) > 0:
            recommendations.append({
                "category": "validation_improvements",
                "priority": "medium",
                "description": f"{len(validation_failures)} validation criteria failed. Review test assertions."
            })
        
        if verification_results["summary"]["success_rate"] < 0.8:
            recommendations.append({
                "category": "test_reliability",
                "priority": "high",
                "description": "Success rate below 80%. Consider improving test stability and environment setup."
            })
        
        return recommendations
    
    def save_report(self, filename: str = None) -> str:
        """Save the QA report to a file."""
        if "summary_report" not in self.current_session:
            raise ValueError("No report available to save. Run QA flow first.")
        
        if filename is None:
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"reports/qa_report_{timestamp}.json"
        
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.current_session["summary_report"], f, indent=2)
        
        print(f"📄 Report saved to: {filename}")
        return filename

def main():
    """Main entry point for the QA flow."""
    parser = argparse.ArgumentParser(description="Run QA Flow with Agent-S + Android World")
    parser.add_argument("--task", default="settings_wifi", 
                       choices=["settings_wifi", "clock_alarm", "email_search"],
                       help="Task to test")
    parser.add_argument("--goal", default="Test turning Wi-Fi on and off in Android settings",
                       help="QA goal description")
    parser.add_argument("--real-device", action="store_true",
                       help="Use real Android device (requires setup)")
    parser.add_argument("--save-report", action="store_true",
                       help="Save detailed report to file")
    
    args = parser.parse_args()
    
    # Initialize QA Flow Manager
    qa_manager = QAFlowManager(
        task_name=args.task,
        enable_real_device=args.real_device
    )
    
    # Run the complete flow
    session_result = qa_manager.run_complete_qa_flow(args.goal)
    
    # Save report if requested
    if args.save_report:
        qa_manager.save_report()
    
    # Print final summary
    print(f"\n{'='*60}")
    print("📋 Final Summary:")
    print(f"Session ID: {session_result['session_id']}")
    print(f"Overall Status: {session_result['overall_status']}")
    print(f"Total Duration: {session_result.get('total_duration', 0):.2f} seconds")
    print(f"Plans Generated: {len(session_result['plans_generated'])}")
    print(f"Executions Completed: {len(session_result['executions_completed'])}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
