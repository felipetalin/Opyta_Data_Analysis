Param(
    [string]$EnvName = "opyta-eco",
    [string]$PythonVersion = "3.11"
)

Write-Host "[1/4] Creating/updating conda environment: $EnvName"
conda create -n $EnvName python=$PythonVersion -y

Write-Host "[2/4] Activating environment"
conda activate $EnvName

Write-Host "[3/4] Installing dependencies"
pip install -r requirements.txt

Write-Host "[4/4] Done"
Write-Host "Set this interpreter in VS Code once and reuse for all projects."
