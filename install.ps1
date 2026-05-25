# Anvar GPT Installer
Write-Host ""
Write-Host "  Installing Anvar GPT..." -ForegroundColor Green

# Create install directory
$installDir = "$env:LOCALAPPDATA\anvar-gpt"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Download exe
$exePath = "$installDir\anvar.exe"
Write-Host "  Downloading anvar.exe..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://github.com/iamfa1ter/anvar-gpt/releases/download/v1.0.0/anvar.exe" -OutFile $exePath

# Add to PATH if not already there
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*anvar-gpt*") {
    [System.Environment]::SetEnvironmentVariable("PATH", "$installDir;$userPath", "User")
    Write-Host "  Added to PATH" -ForegroundColor Cyan
}

# Refresh PATH in current session
$env:PATH = "$installDir;" + $env:PATH

Write-Host ""
Write-Host "  Anvar GPT installed successfully!" -ForegroundColor Green
Write-Host "  Type 'anvar' to start" -ForegroundColor Yellow
Write-Host ""

# Launch it
anvar
