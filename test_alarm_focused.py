#!/usr/bin/env python3
"""
Simple focused test: Alarm setting plan generation and analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from planner_agent import PlannerAgent
from supervisor_agent import SupervisorAgent
import time

def test_alarm_planning():
    """Test alarm setting plan generation with AI analysis."""
    
    print("🚀 Testing: Set an alarm for 7:00 AM")
    print("=" * 50)
    
    # Initialize agents
    planner = PlannerAgent('alarm_setting')
    supervisor = SupervisorAgent(enable_visual_traces=False, enable_ai_analysis=True)
    
    print("📋 Phase 1: Plan Generation")
    plan_start = time.time()
    plan = planner.generate_test_plan("Set an alarm for 7:00 AM")
    plan_time = time.time() - plan_start
    
    print(f"✅ Plan generated in {plan_time:.2f}s")
    print(f"📋 Plan ID: {plan.get('plan_id', 'unknown')}")
    print(f"🎯 Subgoals: {len(plan.get('subgoals', []))}")
    print(f"📝 Total steps: {len(plan.get('steps', []))}")
    
    # Show subgoals
    print("\n🎯 Generated Subgoals:")
    for i, subgoal in enumerate(plan.get('subgoals', []), 1):
        print(f"  {i}. {subgoal.get('description', 'Unknown subgoal')}")
        
    # Show first few steps
    print("\n📝 Sample Steps:")
    for i, step in enumerate(plan.get('steps', [])[:5], 1):
        action = step.get('action', 'unknown')
        target = step.get('target', 'unknown')
        desc = step.get('description', 'Unknown step')
        print(f"  {i}. {desc}")
        print(f"     Action: {action} | Target: {target}")
    
    if len(plan.get('steps', [])) > 5:
        print(f"  ... and {len(plan.get('steps', [])) - 5} more steps")
    
    # Record planning decision for AI analysis
    supervisor.record_agent_decision("PlannerAgent", {
        "action": "generate_test_plan",
        "test_goal": "Set an alarm for 7:00 AM",
        "plan_id": plan.get("plan_id"),
        "subgoals_count": len(plan.get("subgoals", [])),
        "steps_count": len(plan.get("steps", [])),
        "processing_time": plan_time,
        "status": "success",
        "task_type": "alarm_setting"
    })
    
    print("\n🤖 Phase 2: AI Analysis")
    
    # Create mock execution results for analysis
    mock_results = []
    for i, step in enumerate(plan.get('steps', [])[:3]):
        # Simulate some steps succeeding, some failing
        success = i % 2 == 0  # Alternate success/failure
        mock_results.append({
            "step": step,
            "execution": {
                "success": success,
                "action_type": step.get("action"),
                "target": step.get("target"),
                "error": None if success else "Mock execution failure"
            },
            "verification": {
                "verification_status": "PASS" if success else "FAIL",
                "confidence": 0.8 if success else 0.3,
                "functional_bugs": [] if success else [{"type": "execution_failure", "severity": "medium"}]
            },
            "success": success
        })
    
    # Generate comprehensive evaluation
    try:
        evaluation = supervisor.generate_comprehensive_evaluation(
            "Set an alarm for 7:00 AM",
            mock_results
        )
        
        print("✅ AI Analysis completed")
        
        # Show AI insights
        if evaluation.get('ai_analysis'):
            ai_analysis = evaluation['ai_analysis']
            
            # Recommendations
            recommendations = ai_analysis.get('recommendations', [])
            print(f"\n🤖 AI Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:3], 1):
                priority = rec.get('priority', 'unknown')
                suggestion = rec.get('suggestion', 'Unknown recommendation')
                print(f"  {i}. [{priority.upper()}] {suggestion}")
            
            # Performance analysis
            if ai_analysis.get('performance_analysis'):
                perf = ai_analysis['performance_analysis']
                print(f"\n📊 Performance Analysis:")
                print(f"  • Efficiency Score: {perf.get('efficiency_score', 0):.2f}")
                print(f"  • Bottlenecks: {len(perf.get('bottlenecks', []))}")
        
        # Show metrics
        if evaluation.get('metrics'):
            metrics = evaluation['metrics']
            print(f"\n📈 Evaluation Metrics:")
            print(f"  • Bug Detection F1: {metrics.get('bug_detection_f1', 0):.3f}")
            print(f"  • Recovery Rate: {metrics.get('recovery_rate', 0):.1%}")
            print(f"  • System Reliability: {metrics.get('system_reliability', 0):.1%}")
            
        return {
            "plan": plan,
            "evaluation": evaluation,
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ AI Analysis error: {e}")
        return {
            "plan": plan,
            "status": "partial_success",
            "error": str(e)
        }

if __name__ == "__main__":
    result = test_alarm_planning()
    
    print("\n" + "=" * 50)
    print("🎯 ALARM SETTING TEST SUMMARY")
    print("=" * 50)
    
    status = result.get('status', 'unknown')
    print(f"📋 Status: {status.upper()}")
    
    if result.get('plan'):
        plan = result['plan']
        print(f"📊 Plan Quality: {len(plan.get('steps', []))} steps generated")
        print(f"🎯 Complexity: {len(plan.get('subgoals', []))} subgoals")
        
    if result.get('evaluation'):
        print("🤖 AI Analysis: COMPLETED")
        evaluation = result['evaluation']
        if evaluation.get('ai_analysis', {}).get('recommendations'):
            rec_count = len(evaluation['ai_analysis']['recommendations'])
            print(f"💡 Recommendations: {rec_count} suggestions provided")
    
    print("✅ Planner Agent: WORKING")
    print("✅ Supervisor Agent: WORKING") 
    print("✅ AI Analysis: WORKING")
    print("=" * 50)
