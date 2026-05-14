# Script to run primatas pipeline for remaining 3 PCHs
# Execute this after PCH Dores de Guanhães completes

$python = "g:/Meu Drive/Opyta/Opyta_Data_Analysis/.venv/Scripts/python.exe"
$project = 165
$group = "primatas"
$pipeline = "primatas"
$client = "fersam001"
$env_file = "G:/Meu Drive/Opyta/Opyta_Data/.env"
$baseDir = "G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\28_campanha-Abril_26\Primatas"

$pchs = @(
    @("Fortuna II", "Fortuna II"),
    @("Jacaré", "Jacaré"),
    @("Senhora do Porto", "Senhora do Porto")
)

Set-Location "G:\Meu Drive\Opyta\Opyta_Data_Analysis"

foreach ($pch_name, $folder_name in $pchs) {
    $outDir = Join-Path $baseDir $folder_name
    Write-Host "`n[RUN] $pch_name -> $folder_name"
    
    & $python scripts/run_pipeline.py `
        --project-id $project `
        --group $group `
        --pipeline $pipeline `
        --client $client `
        --output-dir $outDir `
        --env-file $env_file `
        --block all
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $pch_name concluído"
    } else {
        Write-Host "✗ Erro ao processar $pch_name"
    }
}

Write-Host "`n✓ Primatas pipeline concluído para todos os 4 PCHs!"
