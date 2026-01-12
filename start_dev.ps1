$env:PYTHONPATH = "$PWD"
Write-Host "Starting StableTrace..."
Write-Host "1. Starting API on port 8000..."
Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "api.main:app --reload --port 8000"
Write-Host "2. Starting Next.js on port 3000..."
Set-Location app
npm run dev
