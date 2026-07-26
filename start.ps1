# ============================================================
# Runs the gemini-java container with mounted projects and
# host credentials (to avoid logging in every time).
#
# Prerequisites:
#   1. Built image: docker build -t gemini-java -f .gemini\sandbox.Dockerfile .
#   2. One-time login on host: gemini  (Login with Google)
# ============================================================

$ErrorActionPreference = "Stop"

# --- Host paths - UPDATE according to your needs ---
$JarvisPath       = "C:\Projects\jarvis"
$SpProdPath       = "C:\Projects\sp-prod"
$SpMetGlobalPath  = "C:\Projects\sp-met-global"
$SpCorePath       = "C:\Projects\sp-core"
$GeminiHomePath   = "$env:USERPROFILE\.gemini"
$ImageName        = "gemini-java"

# --- Quick validation to avoid unreadable Docker errors ---
$pathsToCheck = @($JarvisPath, $SpProdPath, $SpMetGlobalPath, $SpCorePath, $GeminiHomePath)
foreach ($p in $pathsToCheck) {
    if (-not (Test-Path $p)) {
        Write-Warning "Path does not exist: $p (check variables at the top of the script)"
    }
}

# --- Start Host Runner Daemon if not already running ---
$daemonRunning = $null
try {
    $daemonRunning = Get-CimInstance Win32_Process -Filter "Name like '%python%' and CommandLine like '%host_runner.py%'"
} catch {
    # Fallback to Get-Process if CIM is restricted or not working
    $daemonRunning = Get-Process | Where-Object { try { $_.CommandLine -like "*host_runner.py*" } catch { $false } }
}

if (-not $daemonRunning) {
    Write-Host "Starting Host Runner Daemon in background..." -ForegroundColor Green
    $daemonPath = Join-Path $JarvisPath "host_runner.py"
    if (Test-Path $daemonPath) {
        # Run pythonw in hidden window style so it runs silently in the background
        Start-Process -FilePath "pythonw" -ArgumentList "`"$daemonPath`"" -WorkingDirectory $JarvisPath -WindowStyle Hidden
    } else {
        Write-Warning "Host Runner script not found at: $daemonPath"
    }
} else {
    Write-Host "Host Runner Daemon is already running." -ForegroundColor Yellow
}

# --- Load environment variables from .env if present ---
$EnvFileArg = @()
$EnvFilePath = "${JarvisPath}\.env"
if (Test-Path $EnvFilePath) {
    Write-Host "Loading environment variables from $EnvFilePath..." -ForegroundColor Green
    $EnvFileArg = @("--env-file", $EnvFilePath)
}

Write-Host "Starting container '$ImageName'..." -ForegroundColor Cyan

docker run -it --rm `
  @EnvFileArg `
  -v "${JarvisPath}:/workspace/jarvis" `
  -v "${SpProdPath}:/workspace/sp-prod" `
  -v "${SpMetGlobalPath}:/workspace/sp-met-global" `
  -v "${SpCorePath}:/workspace/sp-core:ro" `
  -v "${GeminiHomePath}:/home/node-user/.gemini" `
  -w /workspace/jarvis `
  $ImageName gemini
