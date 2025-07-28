# Android-in-the-Wild Evaluation Usage Guide

## Overview
The Android-in-the-Wild evaluator now supports both **simulation mode** (default) and **live device mode** for comprehensive testing of the multi-agent QA system.

## Execution Modes

### 🟡 Simulation Mode (Default)
- **Safe testing** with no real device actions
- **Faster execution** with realistic success patterns
- **No device required** - works anywhere
- **Perfect for development** and initial testing

### 🔴 Live Mode (--live)
- **Real Android device** execution
- **Actual UI interactions** through Agent-S framework
- **True end-to-end validation**
- **Requires connected Android device**

## Command Line Usage

### Basic Commands

```bash
# Run in simulation mode (default)
python3 android_in_the_wild_evaluator.py

# Run with real Android device
python3 android_in_the_wild_evaluator.py --live

# Test single scenario in simulation
python3 android_in_the_wild_evaluator.py --single

# Test single scenario on real device
python3 android_in_the_wild_evaluator.py --live --single

# Test specific scenario (1-5)
python3 android_in_the_wild_evaluator.py --single --scenario 3
```

### Advanced Usage

```bash
# Live mode with specific scenario (Camera app)
python3 android_in_the_wild_evaluator.py --live --single --scenario 3

# Full comprehensive evaluation on real device
python3 android_in_the_wild_evaluator.py --live
```

## Available Scenarios

1. **Gmail** - Compose and send email with attachment (Medium complexity)
2. **Settings** - Enable dark mode and adjust brightness (Low complexity)  
3. **Camera** - Switch to video mode and record clip (Medium complexity)
4. **Maps** - Search restaurants and get directions (High complexity)
5. **Calendar** - Create recurring meeting with reminders (High complexity)

## Safety Features

### Live Mode Protections
- **User confirmation** required before live execution
- **Step-by-step prompts** for comprehensive evaluation
- **2-second delays** between actions for UI stability
- **Error handling** with graceful fallbacks

### Simulation Mode Benefits
- **No device impact** - completely safe
- **Consistent results** for CI/CD integration
- **Rapid iteration** during development
- **Baseline performance** establishment

## Output Files

Results are automatically saved in two formats:

### JSON Data Files
- `reports/aitw_evaluation_simulation_YYYYMMDD_HHMMSS.json`
- `reports/aitw_evaluation_live_YYYYMMDD_HHMMSS.json`
- Raw evaluation data for programmatic analysis

### Markdown Reports (NEW!)
- `reports/aitw_evaluation_simulation_YYYYMMDD_HHMMSS.md`
- `reports/aitw_evaluation_live_YYYYMMDD_HHMMSS.md`
- **Polished, human-readable reports** perfect for final submissions
- **Professional formatting** with executive summary, performance metrics, and recommendations
- **Visual performance bars** and letter grades for easy assessment
- **Comprehensive analysis** including system readiness and deployment recommendations

## Live Mode Requirements

### Prerequisites
1. **Android device** connected via ADB
2. **Developer options** enabled
3. **USB debugging** enabled
4. **Agent-S framework** properly configured
5. **Device permissions** for target apps

### Setup Verification
```bash
# Check device connection
adb devices

# Verify Agent-S integration
python3 -c "from android_env_wrapper import AndroidEnv; env = AndroidEnv('test', enable_real_device=True); print('✅ Live mode ready')"
```

## Performance Comparison

| Mode | Speed | Accuracy | Real-world Validity | Safety |
|------|-------|----------|-------------------|--------|
| Simulation | ⚡⚡⚡ Fast | 🎯 Consistent | 🟡 Modeled | ✅ Completely Safe |
| Live | 🐌 Slower | 🎯 Variable | ✅ True-to-life | ⚠️ Device Impact |

## Best Practices

### Development Workflow
1. **Start with simulation** for rapid prototyping
2. **Test single scenarios** before comprehensive runs
3. **Validate with live mode** for final verification
4. **Use simulation for CI/CD** pipelines

### Live Mode Guidelines
- **Test with non-production device** when possible
- **Backup device state** before comprehensive runs
- **Monitor device during execution**
- **Have device ready** at the start screen

## Troubleshooting

### Common Issues
- **Device not found**: Check ADB connection and USB debugging
- **Permission errors**: Grant app permissions manually first
- **UI timing issues**: Adjust delays in live mode execution
- **App crashes**: Ensure target apps are installed and updated

### Debug Commands
```bash
# Check Android environment
python3 -c "from android_env_wrapper import AndroidEnv; AndroidEnv.debug_info()"

# Verbose execution with single scenario
python3 android_in_the_wild_evaluator.py --single --scenario 2 --verbose
```

## Integration Examples

### CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Run Android-in-the-Wild Simulation Tests
  run: python3 android_in_the_wild_evaluator.py --single --scenario 2
```

### Local Development
```bash
# Quick development cycle
python3 android_in_the_wild_evaluator.py --single --scenario 1  # Test changes
python3 android_in_the_wild_evaluator.py --live --single --scenario 1  # Validate
```

## Results Analysis

Both modes generate **dual-format output**:

### 📊 JSON Data Files
Raw evaluation data with:
- **Individual scenario scores** (accuracy, robustness, generalization)
- **Execution traces** and agent decisions
- **Performance breakdown** by complexity
- **Comparison metrics** vs ground truth
- **Execution mode metadata** for analysis

### 📋 Markdown Reports (Professional Submission Format)
Polished, publication-ready reports featuring:
- **Executive Summary** with key performance indicators
- **Visual Performance Tables** with letter grades and progress bars
- **Detailed Scenario Analysis** for each test case
- **Technical Analysis** covering multi-agent system performance
- **Statistical Breakdown** including performance distribution
- **System Readiness Assessment** with deployment recommendations
- **Professional Formatting** suitable for stakeholder presentation

The dual-mode system provides the perfect balance of **development velocity** (simulation) and **real-world validation** (live mode) for comprehensive QA automation testing.

### Sample Report Features
- 🎯 **Performance Overview**: Key metrics with A+ to F letter grades
- 📱 **Scenario Details**: Individual app testing with visual performance bars
- 🔧 **Technical Analysis**: Multi-agent system evaluation and recommendations
- 📊 **Statistical Analysis**: Performance distribution and complexity breakdown
- 🚀 **Conclusion**: System readiness assessment and deployment guidance
