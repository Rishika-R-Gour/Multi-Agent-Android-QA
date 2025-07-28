#!/usr/bin/env python3
"""
Evaluation Report Generator
Creates comprehensive evaluation reports for QA automation framework performance.
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics

class EvaluationReportGenerator:
    """
    Generates comprehensive evaluation reports analyzing:
    - Bug detection accuracy across multiple test runs
    - Agent recovery ability and adaptation metrics
    - Supervisor feedback effectiveness
    - Overall system performance trends
    """
    
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        self.ensure_reports_dir()
    
    def ensure_reports_dir(self):
        """Ensure reports directory exists."""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def generate_comprehensive_evaluation_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report analyzing all available data.
        
        Returns:
            Comprehensive evaluation with metrics and analysis
        """
        print("📊 Generating Comprehensive Evaluation Report...")
        
        # Collect all available data
        supervisor_reports = self._collect_supervisor_reports()
        verifier_logs = self._collect_verifier_logs()
        planner_logs = self._collect_planner_logs()
        qa_reports = self._collect_qa_reports()
        
        print(f"📁 Found {len(supervisor_reports)} supervisor reports")
        print(f"📁 Found {len(verifier_logs)} verifier logs")
        print(f"📁 Found {len(planner_logs)} planner logs")
        print(f"📁 Found {len(qa_reports)} QA reports")
        
        # Generate comprehensive analysis
        evaluation_report = {
            "evaluation_id": f"comprehensive_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "data_summary": {
                "supervisor_reports": len(supervisor_reports),
                "verifier_logs": len(verifier_logs),
                "planner_logs": len(planner_logs),
                "qa_reports": len(qa_reports)
            },
            "bug_detection_accuracy": self._analyze_bug_detection_accuracy(supervisor_reports, verifier_logs),
            "agent_recovery_ability": self._analyze_agent_recovery_ability(supervisor_reports, planner_logs),
            "supervisor_feedback_effectiveness": self._analyze_supervisor_effectiveness(supervisor_reports),
            "performance_trends": self._analyze_performance_trends(supervisor_reports, qa_reports),
            "system_reliability": self._analyze_system_reliability(supervisor_reports),
            "recommendations": self._generate_system_recommendations(supervisor_reports, verifier_logs, planner_logs)
        }
        
        # Save comprehensive report
        self._save_evaluation_report(evaluation_report)
        
        return evaluation_report
    
    def _collect_supervisor_reports(self) -> List[Dict[str, Any]]:
        """Collect all supervisor evaluation reports."""
        reports = []
        pattern = os.path.join(self.reports_dir, "supervisor_evaluation_*.json")
        
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    report = json.load(f)
                    reports.append(report)
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
        
        return reports
    
    def _collect_verifier_logs(self) -> List[Dict[str, Any]]:
        """Collect all verifier logs."""
        logs = []
        pattern = os.path.join(self.reports_dir, "qa_verification_log_*.json")
        
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    # Read line by line as each line is a JSON object
                    for line in f:
                        if line.strip():
                            log_entry = json.loads(line.strip())
                            logs.append(log_entry)
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
        
        return logs
    
    def _collect_planner_logs(self) -> List[Dict[str, Any]]:
        """Collect all planner logs."""
        logs = []
        pattern = os.path.join(self.reports_dir, "qa_planner_log_*.json")
        
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    # Read line by line as each line is a JSON object
                    for line in f:
                        if line.strip():
                            log_entry = json.loads(line.strip())
                            logs.append(log_entry)
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
        
        return logs
    
    def _collect_qa_reports(self) -> List[Dict[str, Any]]:
        """Collect all QA reports."""
        reports = []
        pattern = os.path.join(self.reports_dir, "qa_report_*.json")
        
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    report = json.load(f)
                    reports.append(report)
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
        
        return reports
    
    def _analyze_bug_detection_accuracy(self, supervisor_reports: List[Dict], 
                                      verifier_logs: List[Dict]) -> Dict[str, Any]:
        """Analyze bug detection accuracy across all test runs."""
        
        # Aggregate metrics from supervisor reports
        accuracy_metrics = []
        
        for report in supervisor_reports:
            metrics = report.get("metrics", {})
            bug_detection = metrics.get("bug_detection_accuracy", {})
            if bug_detection:
                accuracy_metrics.append(bug_detection)
        
        # Aggregate metrics from verifier logs
        total_bugs_detected = 0
        high_confidence_bugs = 0
        verification_events = 0
        
        for log in verifier_logs:
            if log.get("agent") == "VerifierAgent":
                verification_events += 1
                verification_result = log.get("verification_result", {})
                functional_bugs = verification_result.get("functional_bugs", [])
                
                total_bugs_detected += len(functional_bugs)
                
                for bug in functional_bugs:
                    if bug.get("confidence", 0) > 0.7:
                        high_confidence_bugs += 1
        
        # Calculate aggregated accuracy metrics
        if accuracy_metrics:
            avg_precision = statistics.mean([m.get("precision", 0) for m in accuracy_metrics])
            avg_recall = statistics.mean([m.get("recall", 0) for m in accuracy_metrics])
            avg_f1 = statistics.mean([m.get("f1_score", 0) for m in accuracy_metrics])
        else:
            avg_precision = avg_recall = avg_f1 = 0
        
        # Calculate confidence distribution
        high_confidence_rate = (high_confidence_bugs / max(total_bugs_detected, 1)) * 100
        
        return {
            "aggregated_metrics": {
                "average_precision": avg_precision,
                "average_recall": avg_recall,
                "average_f1_score": avg_f1,
                "total_verification_events": verification_events,
                "total_bugs_detected": total_bugs_detected,
                "high_confidence_detections": high_confidence_bugs,
                "high_confidence_rate": high_confidence_rate
            },
            "accuracy_trend": "improving" if avg_f1 > 0.7 else "needs_improvement",
            "detection_reliability": "high" if high_confidence_rate > 70 else "medium" if high_confidence_rate > 40 else "low"
        }
    
    def _analyze_agent_recovery_ability(self, supervisor_reports: List[Dict], 
                                      planner_logs: List[Dict]) -> Dict[str, Any]:
        """Analyze agent recovery and adaptation capabilities."""
        
        # Analyze recovery metrics from supervisor reports
        recovery_metrics = []
        
        for report in supervisor_reports:
            metrics = report.get("metrics", {})
            recovery_ability = metrics.get("agent_recovery_ability", {})
            if recovery_ability:
                recovery_metrics.append(recovery_ability)
        
        # Analyze replanning events from planner logs
        replanning_events = 0
        successful_replannings = 0
        
        for log in planner_logs:
            if log.get("agent") == "PlannerAgent" and log.get("action") == "dynamic_replanning":
                replanning_events += 1
                if log.get("status") == "completed":
                    successful_replannings += 1
        
        # Calculate aggregated metrics
        if recovery_metrics:
            avg_recovery_rate = statistics.mean([m.get("recovery_success_rate", 0) for m in recovery_metrics])
            avg_adaptation_score = statistics.mean([m.get("adaptation_score", 0) for m in recovery_metrics])
        else:
            avg_recovery_rate = avg_adaptation_score = 0
        
        replanning_success_rate = (successful_replannings / max(replanning_events, 1)) * 100
        
        return {
            "recovery_metrics": {
                "average_recovery_rate": avg_recovery_rate,
                "average_adaptation_score": avg_adaptation_score,
                "total_replanning_events": replanning_events,
                "successful_replannings": successful_replannings,
                "replanning_success_rate": replanning_success_rate
            },
            "adaptation_capability": "excellent" if avg_adaptation_score > 0.8 else "good" if avg_adaptation_score > 0.6 else "needs_improvement",
            "recovery_reliability": "high" if avg_recovery_rate > 0.8 else "medium" if avg_recovery_rate > 0.5 else "low"
        }
    
    def _analyze_supervisor_effectiveness(self, supervisor_reports: List[Dict]) -> Dict[str, Any]:
        """Analyze effectiveness of supervisor feedback and recommendations."""
        
        total_recommendations = 0
        high_priority_recommendations = 0
        prompt_improvements = 0
        coverage_suggestions = 0
        
        processing_times = []
        
        for report in supervisor_reports:
            # Analyze AI analysis results
            ai_analysis = report.get("ai_analysis", {})
            
            if ai_analysis:
                processing_times.append(ai_analysis.get("processing_time", 0))
                
                # Count recommendations
                recommendations = ai_analysis.get("recommendations", [])
                total_recommendations += len(recommendations)
                
                for rec in recommendations:
                    if rec.get("priority") == "high":
                        high_priority_recommendations += 1
                
                # Count prompt improvements
                prompt_improvements += len(ai_analysis.get("prompt_improvements", []))
                
                # Count coverage suggestions
                coverage_analysis = ai_analysis.get("test_coverage", {})
                coverage_suggestions += len(coverage_analysis.get("recommendations", []))
        
        # Calculate effectiveness metrics
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        high_priority_rate = (high_priority_recommendations / max(total_recommendations, 1)) * 100
        
        return {
            "recommendation_metrics": {
                "total_recommendations": total_recommendations,
                "high_priority_recommendations": high_priority_recommendations,
                "high_priority_rate": high_priority_rate,
                "prompt_improvements_suggested": prompt_improvements,
                "coverage_suggestions": coverage_suggestions
            },
            "performance_metrics": {
                "average_processing_time": avg_processing_time,
                "reports_analyzed": len(supervisor_reports)
            },
            "effectiveness_score": min((total_recommendations / max(len(supervisor_reports), 1)) * 0.3 + 
                                     (high_priority_rate / 100) * 0.4 + 
                                     (1 / max(avg_processing_time, 0.1)) * 0.3, 1.0),
            "feedback_quality": "excellent" if high_priority_rate > 30 else "good" if high_priority_rate > 15 else "adequate"
        }
    
    def _analyze_performance_trends(self, supervisor_reports: List[Dict], 
                                  qa_reports: List[Dict]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        
        # Sort reports by timestamp (handle both string and numeric timestamps)
        def safe_timestamp_sort(x):
            timestamp = x.get("timestamp", "")
            if isinstance(timestamp, (int, float)):
                return str(timestamp)
            return str(timestamp)
        
        supervisor_reports.sort(key=safe_timestamp_sort)
        qa_reports.sort(key=safe_timestamp_sort)
        
        # Extract performance metrics over time
        success_rates = []
        test_durations = []
        bug_detection_scores = []
        
        for report in supervisor_reports:
            # Success rate
            statistics_data = report.get("statistics", {})
            success_rate = statistics_data.get("test_success_rate", 0)
            success_rates.append(success_rate)
            
            # Test duration
            qa_metrics = report.get("qa_flow_metrics", {})
            duration = qa_metrics.get("total_test_duration", 0)
            test_durations.append(duration)
            
            # Bug detection score
            metrics = report.get("metrics", {})
            bug_detection = metrics.get("bug_detection_accuracy", {})
            f1_score = bug_detection.get("f1_score", 0)
            bug_detection_scores.append(f1_score)
        
        # Calculate trends
        success_rate_trend = self._calculate_trend(success_rates)
        duration_trend = self._calculate_trend(test_durations)
        detection_trend = self._calculate_trend(bug_detection_scores)
        
        return {
            "success_rate_trend": {
                "direction": success_rate_trend,
                "values": success_rates,
                "current_average": statistics.mean(success_rates[-3:]) if len(success_rates) >= 3 else statistics.mean(success_rates) if success_rates else 0
            },
            "duration_trend": {
                "direction": duration_trend,
                "values": test_durations,
                "current_average": statistics.mean(test_durations[-3:]) if len(test_durations) >= 3 else statistics.mean(test_durations) if test_durations else 0
            },
            "detection_trend": {
                "direction": detection_trend,
                "values": bug_detection_scores,
                "current_average": statistics.mean(bug_detection_scores[-3:]) if len(bug_detection_scores) >= 3 else statistics.mean(bug_detection_scores) if bug_detection_scores else 0
            },
            "overall_trend": "improving" if (success_rate_trend == "improving" and detection_trend == "improving") else "stable" if success_rate_trend == "stable" else "declining"
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values."""
        if len(values) < 3:
            return "insufficient_data"
        
        # Compare recent average to earlier average
        recent_avg = statistics.mean(values[-3:])
        earlier_avg = statistics.mean(values[:-3]) if len(values) > 3 else statistics.mean(values[:3])
        
        improvement_threshold = 0.05  # 5% improvement threshold
        
        if recent_avg > earlier_avg + improvement_threshold:
            return "improving"
        elif recent_avg < earlier_avg - improvement_threshold:
            return "declining"
        else:
            return "stable"
    
    def _analyze_system_reliability(self, supervisor_reports: List[Dict]) -> Dict[str, Any]:
        """Analyze overall system reliability and stability."""
        
        total_tests = len(supervisor_reports)
        successful_tests = len([r for r in supervisor_reports if r.get("overall_status") == "PASS"])
        
        # Analyze failure patterns
        failure_types = {}
        for report in supervisor_reports:
            if report.get("overall_status") == "FAIL":
                ai_analysis = report.get("ai_analysis")
                if ai_analysis:  # Check if ai_analysis exists
                    failure_analysis = ai_analysis.get("failure_analysis", {})
                    failure_type_data = failure_analysis.get("failure_types", {})
                    
                    for failure_type, count in failure_type_data.items():
                        failure_types[failure_type] = failure_types.get(failure_type, 0) + count
        
        # Calculate reliability metrics
        system_reliability = (successful_tests / max(total_tests, 1)) * 100
        
        # Determine stability rating
        if system_reliability > 90:
            stability_rating = "excellent"
        elif system_reliability > 75:
            stability_rating = "good"
        elif system_reliability > 60:
            stability_rating = "acceptable"
        else:
            stability_rating = "needs_improvement"
        
        return {
            "reliability_metrics": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "system_reliability_percentage": system_reliability,
                "failure_types": failure_types
            },
            "stability_rating": stability_rating,
            "reliability_trend": "stable" if system_reliability > 70 else "concerning"
        }
    
    def _generate_system_recommendations(self, supervisor_reports: List[Dict], 
                                       verifier_logs: List[Dict], 
                                       planner_logs: List[Dict]) -> List[Dict[str, Any]]:
        """Generate system-wide recommendations based on comprehensive analysis."""
        
        recommendations = []
        
        # Analyze common issues across all reports
        common_issues = self._identify_common_issues(supervisor_reports)
        
        # Agent-specific recommendations
        if len([log for log in verifier_logs if log.get("verification_result", {}).get("functional_bugs")]) > len(verifier_logs) * 0.3:
            recommendations.append({
                "category": "bug_detection",
                "priority": "high",
                "title": "Improve verifier accuracy",
                "description": "High number of bug detections may indicate false positives",
                "actions": [
                    "Calibrate verifier confidence thresholds",
                    "Add more sophisticated heuristic checks",
                    "Implement ground truth validation"
                ]
            })
        
        # Replanning frequency recommendations
        replanning_frequency = len([log for log in planner_logs if "replanning" in log.get("action", "")])
        if replanning_frequency > len(planner_logs) * 0.2:
            recommendations.append({
                "category": "planning",
                "priority": "medium",
                "title": "Reduce replanning frequency",
                "description": f"High replanning frequency ({replanning_frequency} events) indicates planning issues",
                "actions": [
                    "Improve initial plan quality",
                    "Add better modal state prediction",
                    "Enhance error prevention strategies"
                ]
            })
        
        # Performance recommendations
        duration_data = [
            r.get("qa_flow_metrics", {}).get("total_test_duration", 0) 
            for r in supervisor_reports 
            if r.get("qa_flow_metrics", {}).get("total_test_duration")
        ]
        
        avg_duration = statistics.mean(duration_data) if duration_data else 0
        
        if avg_duration > 30:  # More than 30 seconds
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "title": "Optimize test execution time",
                "description": f"Average test duration of {avg_duration:.1f}s is above optimal range",
                "actions": [
                    "Optimize agent decision times",
                    "Implement parallel verification where possible",
                    "Reduce unnecessary wait times"
                ]
            })
        
        return recommendations
    
    def _identify_common_issues(self, supervisor_reports: List[Dict]) -> Dict[str, int]:
        """Identify common issues across all supervisor reports."""
        
        issues = {}
        
        for report in supervisor_reports:
            ai_analysis = report.get("ai_analysis")
            if ai_analysis:  # Check if ai_analysis exists
                prompt_improvements = ai_analysis.get("prompt_improvements", [])
                
                for improvement in prompt_improvements:
                    issue = improvement.get("issue", "unknown")
                    issues[issue] = issues.get(issue, 0) + 1
        
        return issues
    
    def _save_evaluation_report(self, evaluation_report: Dict[str, Any]):
        """Save comprehensive evaluation report."""
        
        timestamp = evaluation_report["evaluation_id"].split("_")[-2:]
        timestamp_str = "_".join(timestamp)
        
        # Save detailed JSON
        json_path = os.path.join(self.reports_dir, f"comprehensive_evaluation_{timestamp_str}.json")
        with open(json_path, 'w') as f:
            json.dump(evaluation_report, f, indent=2, default=str)
        
        # Generate summary markdown
        md_path = os.path.join(self.reports_dir, f"evaluation_summary_{timestamp_str}.md")
        self._generate_summary_markdown(evaluation_report, md_path)
        
        print(f"\n📊 Comprehensive Evaluation Report Generated:")
        print(f"   📄 Detailed JSON: {json_path}")
        print(f"   📝 Summary Markdown: {md_path}")
        
        # Print key findings
        self._print_key_findings(evaluation_report)
    
    def _generate_summary_markdown(self, evaluation_report: Dict[str, Any], output_path: str):
        """Generate summary markdown report."""
        
        md_content = f"""# Comprehensive QA System Evaluation Report

**Evaluation ID:** {evaluation_report['evaluation_id']}  
**Generated:** {evaluation_report['timestamp']}

## Executive Summary

### Data Analysis
- **Supervisor Reports:** {evaluation_report['data_summary']['supervisor_reports']}
- **Verifier Logs:** {evaluation_report['data_summary']['verifier_logs']}
- **Planner Logs:** {evaluation_report['data_summary']['planner_logs']}
- **QA Reports:** {evaluation_report['data_summary']['qa_reports']}

### Key Metrics

#### Bug Detection Accuracy
- **Average F1 Score:** {evaluation_report['bug_detection_accuracy']['aggregated_metrics']['average_f1_score']:.3f}
- **Detection Reliability:** {evaluation_report['bug_detection_accuracy']['detection_reliability']}
- **Total Bugs Detected:** {evaluation_report['bug_detection_accuracy']['aggregated_metrics']['total_bugs_detected']}

#### Agent Recovery Ability
- **Recovery Success Rate:** {evaluation_report['agent_recovery_ability']['recovery_metrics']['average_recovery_rate']:.2%}
- **Adaptation Capability:** {evaluation_report['agent_recovery_ability']['adaptation_capability']}
- **Replanning Events:** {evaluation_report['agent_recovery_ability']['recovery_metrics']['total_replanning_events']}

#### Supervisor Effectiveness
- **Effectiveness Score:** {evaluation_report['supervisor_feedback_effectiveness']['effectiveness_score']:.3f}
- **Feedback Quality:** {evaluation_report['supervisor_feedback_effectiveness']['feedback_quality']}
- **Total Recommendations:** {evaluation_report['supervisor_feedback_effectiveness']['recommendation_metrics']['total_recommendations']}

#### System Reliability
- **System Reliability:** {evaluation_report['system_reliability']['reliability_metrics']['system_reliability_percentage']:.1f}%
- **Stability Rating:** {evaluation_report['system_reliability']['stability_rating']}

### Performance Trends
- **Success Rate Trend:** {evaluation_report['performance_trends']['success_rate_trend']['direction']}
- **Duration Trend:** {evaluation_report['performance_trends']['duration_trend']['direction']}
- **Detection Trend:** {evaluation_report['performance_trends']['detection_trend']['direction']}
- **Overall Trend:** {evaluation_report['performance_trends']['overall_trend']}

## Recommendations
"""
        
        for rec in evaluation_report['recommendations']:
            md_content += f"\n### {rec['title']} ({rec['priority']} priority)\n"
            md_content += f"{rec['description']}\n\n"
            md_content += "Actions:\n"
            for action in rec['actions']:
                md_content += f"- {action}\n"
            md_content += "\n"
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _print_key_findings(self, evaluation_report: Dict[str, Any]):
        """Print key findings to console."""
        
        print("\n" + "="*60)
        print("🎯 KEY EVALUATION FINDINGS")
        print("="*60)
        
        # Bug detection
        bug_accuracy = evaluation_report['bug_detection_accuracy']['aggregated_metrics']['average_f1_score']
        print(f"🔍 Bug Detection F1 Score: {bug_accuracy:.3f}")
        
        # Recovery ability
        recovery_rate = evaluation_report['agent_recovery_ability']['recovery_metrics']['average_recovery_rate']
        print(f"🔄 Agent Recovery Rate: {recovery_rate:.2%}")
        
        # System reliability
        reliability = evaluation_report['system_reliability']['reliability_metrics']['system_reliability_percentage']
        print(f"⚡ System Reliability: {reliability:.1f}%")
        
        # Trends
        overall_trend = evaluation_report['performance_trends']['overall_trend']
        trend_emoji = "📈" if overall_trend == "improving" else "📊" if overall_trend == "stable" else "📉"
        print(f"{trend_emoji} Overall Trend: {overall_trend}")
        
        # Top recommendation
        recommendations = evaluation_report['recommendations']
        if recommendations:
            top_rec = recommendations[0]
            print(f"💡 Top Recommendation: {top_rec['title']} ({top_rec['priority']} priority)")
        
        print("="*60)

def main():
    """Generate comprehensive evaluation report."""
    
    print("📊 QA System Comprehensive Evaluation")
    print("=====================================")
    
    # Initialize generator
    generator = EvaluationReportGenerator()
    
    # Generate comprehensive report
    evaluation_report = generator.generate_comprehensive_evaluation_report()
    
    print("\n✅ Comprehensive evaluation completed!")
    return evaluation_report

if __name__ == "__main__":
    main()
