# =================================================================
# Automated Dice Job Application - Scheduled Task Setup Script
# Creates a Windows Task Scheduler job that runs every 6 hours
# =================================================================

param(
    [string]$TaskName = "Dice-Headless-Automation",
    [string]$ProjectPath = $null,
    [switch]$Force
)

# If project path not provided, use current directory
if (-not $ProjectPath) {
    $ProjectPath = $PSScriptRoot
}

$BatchFile = Join-Path $ProjectPath "run_headless_scheduled.bat"
$TaskDescription = "Runs headless Dice job automation every 6 hours"

Write-Host "Setting up scheduled task for Dice automation..." -ForegroundColor Green
Write-Host "Project Path: $ProjectPath" -ForegroundColor Cyan
Write-Host "Batch File: $BatchFile" -ForegroundColor Cyan

# Check if batch file exists
if (-not (Test-Path $BatchFile)) {
    Write-Error "Batch file not found: $BatchFile"
    Write-Host "Please ensure run_headless_scheduled.bat exists in the project directory." -ForegroundColor Yellow
    exit 1
}

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask -and -not $Force) {
    Write-Warning "Task '$TaskName' already exists. Use -Force to recreate it."
    exit 1
}

# Remove existing task if Force is specified
if ($existingTask -and $Force) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create new scheduled task
Write-Host "Creating scheduled task..." -ForegroundColor Green

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchFile`"" -WorkingDirectory $ProjectPath
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType InteractiveToken

try {
    $task = Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $TaskDescription

    if ($task) {
        Write-Host "SUCCESS: Scheduled task '$TaskName' created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Task Details:" -ForegroundColor Yellow
        Write-Host "  - Runs every 6 hours starting from now" -ForegroundColor Cyan
        Write-Host "  - Executes: $BatchFile" -ForegroundColor Cyan
        Write-Host "  - Working Directory: $ProjectPath" -ForegroundColor Cyan
        Write-Host "  - Runs even when on battery power" -ForegroundColor Cyan
        Write-Host "  - Starts automatically if missed while computer was off" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To modify the task:" -ForegroundColor Yellow
        Write-Host "  1. Open Task Scheduler (taskschd.msc)" -ForegroundColor Cyan
        Write-Host "  2. Navigate to Task Scheduler Library" -ForegroundColor Cyan
        Write-Host "  3. Find and double-click '$TaskName'" -ForegroundColor Cyan
        Write-Host "  4. Adjust triggers, actions, or conditions as needed" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To test the task immediately:" -ForegroundColor Yellow
        Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
    }
} catch {
    Write-Error "Failed to create scheduled task: $($_.Exception.Message)"
    exit 1
}
