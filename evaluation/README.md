# Evaluation and Benchmarking Directory

This directory contains specialized evaluation and benchmarking tools for the Multi-Agent Android QA system, separated from the core agent implementations for better project organization.

## 📁 Contents

### `android_in_the_wild_evaluator.py`
**Bonus Feature**: Android-in-the-Wild Dataset Integration
- Comprehensive evaluation framework against real user session traces
- Supports both simulation mode (default) and live device mode (`--live`)
- 5 complete test scenarios covering different Android apps and complexity levels
- Multi-dimensional scoring: accuracy, robustness, and generalization
- Professional markdown report generation

**Usage:**
```bash
# Navigate to evaluation directory
cd evaluation

# Run in simulation mode (safe, no device impact)
python3 android_in_the_wild_evaluator.py

# Run with real Android device
python3 android_in_the_wild_evaluator.py --live

# Test single scenario for development
python3 android_in_the_wild_evaluator.py --single --scenario 2
```

### `evaluation_report_generator.py`
**System Performance Analysis**
- Comprehensive evaluation report generation
- Multi-run performance trend analysis
- Bug detection accuracy metrics
- Agent recovery capability assessment
- Supervisor feedback effectiveness analysis

**Usage:**
```bash
# Generate comprehensive evaluation report
python3 evaluation_report_generator.py

# Analyze specific report files
python3 evaluation_report_generator.py --input reports/
```

## 🔧 Technical Notes

### Import Path Configuration
Both evaluation scripts automatically configure their import paths to access core agents:
```python
# Add core directory to path for agent imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'core'))
```

### Dependencies
- Requires all core agents: `supervisor_agent`, `planner_agent`, `new_executor_agent`, `verifier_agent`
- Uses `android_env_wrapper` for Android environment simulation
- Compatible with both simulation and live device modes

## 📊 Performance Results

**Latest Android-in-the-Wild Evaluation:**
- **Overall Performance**: 90.7% (Grade A)
- **Accuracy**: 100.0% (Grade A+)
- **Robustness**: 82.0% (Grade B+)
- **Generalization**: 90.0% (Grade A)

## 🎯 Evaluation Scenarios

1. **Gmail** - Compose and send email with attachment (Medium complexity)
2. **Settings** - Enable dark mode and adjust display brightness (Low complexity)
3. **Camera** - Switch to video mode and record 10-second clip (Medium complexity)
4. **Maps** - Search for nearby restaurants and get directions (High complexity)
5. **Calendar** - Create recurring weekly meeting with notification reminder (High complexity)

## 📋 Reports Generated

All evaluation reports are saved to the `../reports/` directory:
- **JSON Format**: `aitw_evaluation_[mode]_[timestamp].json`
- **Markdown Format**: `aitw_evaluation_[mode]_[timestamp].md`

---

*This evaluation system demonstrates the multi-agent QA framework's capability to handle real-world Android application testing scenarios with professional-grade performance metrics and comprehensive reporting.*
