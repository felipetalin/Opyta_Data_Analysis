param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Configuring remote origin..." -ForegroundColor Cyan
git remote add origin $RemoteUrl

Write-Host "Pushing main branch..." -ForegroundColor Cyan
git push -u origin main

Write-Host "Pushing release tag v0.1.0..." -ForegroundColor Cyan
git push origin v0.1.0

Write-Host "Done. Repository published with main + v0.1.0." -ForegroundColor Green
