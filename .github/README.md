# 🤖 GitHub Actions CI/CD Setup - Dice Job Automation

## Overview

This setup provides a complete CI/CD pipeline using GitHub Actions that runs your Dice job automation every 6 hours with comprehensive Slack notifications and detailed reporting.

## 📁 Project Structure

```
.github/
├── workflows/
│   ├── dice-automation.yml      # Main automation workflow (runs every 6 hours)
│   └── test-dice-setup.yml      # Setup validation workflow
└── env-template.txt             # Environment variables template

scripts/
└── run_headless_scheduled.bat   # Enhanced automation script with reporting
```

## 🚀 Quick Setup

### 1. Configure Repository Secrets

Add these secrets to your GitHub repository (`Settings → Secrets and variables → Actions`):

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `SLACK_WEBHOOK_URL` | Your Slack webhook URL | Yes |
| `DICE_EMAIL` | Your Dice account email | Yes |
| `DICE_PASSWORD` | Your Dice account password | Yes |

### 2. Enable the Workflow

The main workflow is automatically triggered by:
- **Schedule**: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
- **Manual trigger**: Via GitHub Actions UI
- **Code changes**: When scripts or workflow files are modified

### 3. Test the Setup

Run the test workflow manually:
1. Go to `Actions` tab in your repository
2. Select `Test Dice Automation Setup` workflow
3. Click `Run workflow`

## 📊 Features

### ✅ Automated Execution
- Runs every 6 hours automatically
- Windows-based execution environment
- Proper dependency management with `uv`
- Virtual environment handling

### 📈 Comprehensive Reporting
- **Job Statistics**: Attempted, succeeded, failed counts
- **Execution Summary**: Start/end times, duration
- **Error Details**: Detailed failure information
- **Log Management**: Automatic cleanup after 7 days

### 💬 Slack Notifications
- **Success notifications** with green checkmark
- **Failure notifications** with red X
- **Detailed summaries** including execution stats
- **Log file links** for troubleshooting

### 🔧 Advanced Features
- **Artifact uploads**: Logs and summaries saved for 7 days
- **PR comments**: Automatic comments on code changes
- **Error handling**: Robust error catching and reporting
- **Environment validation**: Checks for required credentials

## 🛠️ Customization

### Change Schedule
Edit `.github/workflows/dice-automation.yml`:
```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
```

### Modify Notifications
Update the Slack payload in the workflow:
```yaml
- name: Send Slack notification
  run: |
    # Customize the notification format here
```

### Environment Variables
Add more configuration via repository secrets:
```bash
# Additional secrets you can add:
MAX_APPLICATIONS_PER_RUN=10
DICE_SEARCH_TERMS=python,developer
LOG_LEVEL=INFO
```

## 📋 Workflow Details

### Main Workflow (`dice-automation.yml`)

1. **Environment Setup**
   - Installs Python 3.11 and `uv` package manager
   - Creates and activates virtual environment
   - Installs project dependencies

2. **Script Execution**
   - Runs the automation script with timeout (60 minutes)
   - Continues on error for proper reporting
   - Captures execution results

3. **Artifact Management**
   - Uploads logs and summaries as downloadable artifacts
   - Retains for 7 days for troubleshooting

4. **Notification System**
   - Reads job summary from JSON file
   - Sends formatted Slack notifications
   - Comments on PRs when triggered by pushes

### Test Workflow (`test-dice-setup.yml`)

1. **Validation Checks**
   - Verifies script file exists
   - Tests environment setup
   - Validates credentials configuration

2. **Test Notifications**
   - Sends test Slack message
   - Creates sample summary file

## 🔍 Monitoring and Troubleshooting

### View Execution History
- **GitHub Actions**: `Actions` tab → Workflow runs
- **Artifacts**: Download logs from successful/failed runs
- **PR Comments**: Automatic comments on code changes

### Log Analysis
Logs include:
- Execution timestamps
- Environment setup details
- Script output and errors
- Summary generation
- Slack notification status

### Common Issues

1. **Authentication Errors**
   - Verify `DICE_EMAIL` and `DICE_PASSWORD` secrets
   - Check Dice account status

2. **Dependency Issues**
   - Ensure `uv` installation works
   - Check virtual environment creation

3. **Network/Slack Issues**
   - Verify `SLACK_WEBHOOK_URL` format
   - Check network connectivity in workflow

## 🔐 Security Considerations

- **Secrets Management**: All credentials stored as GitHub secrets
- **Environment Variables**: No hardcoded sensitive data
- **Artifact Security**: Logs don't contain credentials
- **Access Control**: Workflow runs in isolated environment

## 📞 Support

### Getting Help
1. Check the `Actions` tab for workflow run details
2. Download and analyze log artifacts
3. Review the `test-dice-setup.yml` workflow for diagnostics
4. Check Slack notifications for execution summaries

### Emergency Stop
To temporarily disable the automation:
1. Go to `Actions` tab
2. Click `Disable workflow` on the main workflow
3. Or modify the cron schedule in the workflow file

## 🔄 Maintenance

### Regular Tasks
- Monitor execution success rate
- Review and rotate credentials periodically
- Update dependencies as needed
- Clean up old artifacts

### Updates and Improvements
- Modify notification format in workflow
- Adjust execution parameters
- Add new environment variables
- Enhance error handling

---

**🎯 Result**: Your Dice job automation now runs automatically every 6 hours with comprehensive monitoring and notifications!
