#!/usr/bin/env python3
"""
Simple test: Set an alarm with full Supervisor monitoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supervisor_agent import SupervisorAgent
from planner_agent import PlannerAgent
from new_executor_agent import EnhancedExecutorAgent
from verifier_agent import VerifierAgent
from android_env_wrapper import AndroidEnv
import time

def test_alarm_setting():
    """Test setting an alarm with full monitoring."""
    
    print("🚀 Testing: Set an alarm for 7:00 AM")
    print("=" * 50)
    
    # Initialize agents
    supervisor = SupervisorAgent(enable_visual_traces=True, enable_ai_analysis=True)
    planner = PlannerAgent('alarm_setting')
    executor = EnhancedExecutorAgent('alarm_setting')
    verifier = VerifierAgent('alarm_setting')
    env = AndroidEnv('alarm_setting', enable_real_device=False)
    
    # Start supervision session
    session_id = supervisor.start_supervision_session("Set an alarm for 7:00 AM", "alarm_setting")
    print(f"📋 Session ID: {session_id}")
    
    try:
        # Phase 1: Planning
        print("\n📋 Phase 1: Planning")
        plan_start = time.time()
        plan = planner.generate_test_plan("Set an alarm for 7:00 AM")
        plan_time = time.time() - plan_start
        
        supervisor.record_agent_decision("PlannerAgent", {
            "action": "generate_test_plan",
            "test_goal": "Set an alarm for 7:00 AM",
            "plan_id": plan.get("plan_id"),
            "subgoals_count": len(plan.get("subgoals", [])),
            "steps_count": len(plan.get("steps", [])),
            "processing_time": plan_time,
            "status": "success"
        })
        
        print(f"✅ Plan generated: {len(plan.get('steps', []))} steps")
        print(f"🎯 Subgoals: {len(plan.get('subgoals', []))}")
        
        # Phase 2: Execute first few steps with monitoring
        print("\n⚡ Phase 2: Execution (First 3 steps)")
        execution_results = []
        
        for i, step in enumerate(plan.get('steps', [])[:3], 1):
            print(f"\n📝 Step {i}: {step.get('description', 'Unknown step')}")
            
            # Get environment state
            env_state = env.get_state()
            supervisor.capture_environment_state(env_state)
            
            # Execute step
            exec_start = time.time()
            exec_result = executor.execute_step(step, env_state)
            exec_time = time.time() - exec_start
            
            # Record execution
            supervisor.record_agent_decision("ExecutorAgent", {
                "action": "execute_step",
                "step_id": step.get("step_id"),
                "step_description": step.get("description"),
                "success": exec_result.get("success", False),
                "processing_time": exec_time,
                "target": step.get("target"),
                "action_type": step.get("action")
            })
            
            # Verify step
            verify_start = time.time()
            verification = verifier.verify_goal_state(
                {"goal": step.get("description")},
                env_state,
                exec_result
            )
            verify_time = time.time() - verify_start
            
            # Record verification
            supervisor.record_agent_decision("VerifierAgent", {
                "action": "verify_step",
                "step_id": step.get("step_id"),
                "verification_status": verification.get("verification_status"),
                "bugs_detected": len(verification.get("functional_bugs", [])),
                "confidence": verification.get("confidence", 0),
                "processing_time": verify_time
            })
            
            # Show result
            step_success = (exec_result.get("success", False) and 
                          verification.get("verification_status") == "PASS")
            status_emoji = "✅" if step_success else "❌"
            print(f"{status_emoji} Result: {'PASS' if step_success else 'FAIL'}")
            
            execution_results.append({
                "step": step,
                "execution": exec_result,
                "verification": verification,
                "success": step_success
            })
            
            time.sleep(0.2)  # Brief pause
        
        # Phase 3: Comprehensive Evaluation
        print("\n📊 Phase 3: Supervisor Evaluation")
        
        final_results = [r for r in execution_results]
        evaluation = supervisor.generate_comprehensive_evaluation(
            "Set an alarm for 7:00 AM", 
            final_results
        )
        
        print(f"✅ Evaluation completed")
        print(f"🤖 AI Analysis: {'Available' if evaluation.get('ai_analysis') else 'Not available'}")
        print(f"📊 Metrics calculated: {len(evaluation.get('metrics', {}))}")
        print(f"📸 Visual frames: {evaluation.get('visual_traces', {}).get('total_frames', 0)}")
        
        # Show key metrics
        if evaluation.get('metrics'):
            metrics = evaluation['metrics']
            print(f"\n📈 Key Metrics:")
            print(f"  • Bug Detection F1: {metrics.get('bug_detection_f1', 0):.3f}")
            print(f"  • Recovery Rate: {metrics.get('recovery_rate', 0):.1%}")
            print(f"  • System Reliability: {metrics.get('system_reliability', 0):.1%}")
        
        # Show AI recommendations
        if evaluation.get('ai_analysis', {}).get('recommendations'):
            recommendations = evaluation['ai_analysis']['recommendations']
            print(f"\n🤖 AI Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec.get('suggestion', 'Unknown recommendation')}")
        
        return {
            "session_id": session_id,
            "plan": plan,
            "execution_results": execution_results,
            "evaluation": evaluation,
            "status": "completed"
        }
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return {"status": "error", "error": str(e)}
    
    finally:
        # End supervision session  
        try:
            supervisor.end_supervision_session()
        except:
            pass  # Session may not have started properly

if __name__ == "__main__":
    result = test_alarm_setting()
    
    print("\n" + "=" * 50)
    print("🎯 ALARM SETTING TEST SUMMARY")
    print("=" * 50)
    print(f"📋 Status: {result.get('status', 'unknown').upper()}")
    if result.get('execution_results'):
        success_count = sum(1 for r in result['execution_results'] if r.get('success'))
        total_count = len(result['execution_results'])
        print(f"📊 Steps: {success_count}/{total_count} successful")
        print(f"📈 Success Rate: {success_count/total_count:.1%}")
    print("=" * 50)
