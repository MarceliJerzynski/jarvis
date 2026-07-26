$ErrorActionPreference = "Stop"

Write-Host "Building Docker image 'gemini-java' using .gemini\sandbox.Dockerfile..." -ForegroundColor Cyan

docker build --no-cache -t gemini-java -f .gemini\sandbox.Dockerfile .

Write-Host "Image successfully built!" -ForegroundColor Green
