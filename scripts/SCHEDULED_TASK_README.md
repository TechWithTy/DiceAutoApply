# CI/CD Cron Job Setup - Dice Headless Automation

## Overview
This setup creates a Windows Task Scheduler job that runs the headless Dice automation every 6 hours.

## Files Created
- `run_headless_scheduled.bat` - Enhanced batch file with error handling and logging
- `setup_scheduled_task.ps1` - PowerShell script for automated task creation
- `Dice-Headless-Automation.xml` - Task Scheduler XML template

## Quick Setup (Automated)

1. **Open PowerShell as Administrator**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Run the setup script**
   ```powershell
   .\setup_scheduled_task.ps1
   ```

3. **Verify the task was created**
   - Open Task Scheduler (`taskschd.msc`)
   - Navigate to **Task Scheduler Library**
   - Look for **Dice-Headless-Automation**

## Manual Setup (Alternative Method)

### Step 1: Create the Task
1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **Create Task** (not "Create Basic Task")
3. General tab:
   - Name: `Dice-Headless-Automation`
   - Description: `Runs headless Dice job automation every 6 hours`
   - Check: `Run with highest privileges`
   - Select: `Run whether user is logged on or not`

### Step 2: Configure Triggers
1. **Triggers** tab → **New**
2. Begin the task: `On a schedule`
3. Settings:
   - Daily
   - Recur every: `1` days
   - Repeat task every: `6 hours`
   - Indefinitely
   - Enabled: `True`

### Step 3: Configure Actions
1. **Actions** tab → **New**
2. Action: `Start a program`
3. Program/script: `cmd.exe`
4. Arguments: `/c "[PROJECT_PATH]\run_headless_scheduled.bat"`
5. Start in: `[PROJECT_PATH]`

### Step 4: Configure Conditions
1. **Conditions** tab:
   - Uncheck: `Start the task only if the computer is on AC power`
   - Check: `Wake the computer to run this task`
   - Check: `Start only if the following network connection is available` → `Any connection`

### Step 5: Configure Settings
1. **Settings** tab:
   - Check: `Allow task to be run on demand`
   - Check: `Run task as soon as possible after a scheduled start is missed`
   - Check: `If the task fails, restart every` → `5 minutes`, `3` attempts
   - Check: `Stop the task if it runs longer than` → `1 hour`
   - Check: `If the running task does not end when requested, force it to stop`

## Testing the Setup

### Test the Batch File
```cmd
.\run_headless_scheduled.bat
```

### Test the Scheduled Task
```powershell
Start-ScheduledTask -TaskName "Dice-Headless-Automation"
```

## Monitoring and Logs

- **Log Location**: `logs/headless_run_YYYYMMDD_HHMMSS.log`
- **Task History**: Task Scheduler → Right-click task → View History
- **Manual Execution**: Right-click task → Run

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure the batch file is not marked as read-only
   - Run PowerShell/Command Prompt as Administrator

2. **Path Issues**
   - Use absolute paths in the task configuration
   - Ensure the project directory path is correct

3. **Virtual Environment Issues**
   - The batch file will use the virtual environment if it exists
   - If missing, it falls back to system Python

4. **Network Issues**
   - The task requires network connectivity
   - Check network conditions in Task Scheduler

### Log Analysis
- Check the log files in the `logs` directory for errors
- Look for exit codes and error messages
- Verify that the virtual environment activation worked

## Customization

### Change Schedule
- Edit the trigger in Task Scheduler
- Modify the repetition interval in the PowerShell script

### Change Log Retention
- Edit the `forfiles` command in the batch file
- Currently keeps logs for 7 days

### Add Email Notifications
- Modify the batch file to send emails on success/failure
- Use PowerShell's `Send-MailMessage` cmdlet

## Security Notes

- The task runs with your user privileges
- Ensure `.env` file contains necessary credentials
- Consider using Windows Credential Manager for sensitive data
- The headless script should handle authentication securely

## Maintenance

- Regularly check log files for errors
- Monitor Task Scheduler event logs
- Update the automation script as needed
- Test the setup after system updates
