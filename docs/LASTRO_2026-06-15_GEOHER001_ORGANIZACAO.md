# Lastro 2026-06-15 - GEOHER001 e organizacao do repositorio

## Contexto

Fechamento tecnico das atividades de 2026-06-15 relacionadas a:

- analises do recorte GEOHER001/Herculano 2022-2025;
- ajustes de pipeline para Ictiofauna e Zoobentos;
- correcao do indicador EPT/CHOL em Zoobentos;
- reorganizacao dos scripts operacionais do repositorio;
- criacao de controle para nao perder historico, scripts, patterns e recipes.

## Principais entregas

- Recipe criada: `configs/projects/geoher001_herculano_2022_2025.json`.
- Configuracao visual criada: `configs/clients/geoher001.json`.
- Nota de projeto criada: `docs/projects/GEOHER001_HERCULANO_2022_2025.md`.
- Padroes documentados em `docs/patterns/`.
- Scripts organizados em `scripts/projects`, `scripts/migrations`, `scripts/run`,
  `scripts/validation`, `scripts/maintenance` e `scripts/prototypes`.
- Wrappers temporarios mantidos na raiz de `scripts/` via `scripts/_compat.py`.
- Checklist criado: `docs/CHECKLIST_PROJETO.md`.
- Validador criado: `scripts/validation/check_repo_organization.py`.

## Balanço registrado pelo validador

Comando:

```powershell
python scripts\validation\check_repo_organization.py
```

Resultado em 2026-06-15:

- recipes de projeto: 1;
- notas em `docs/projects`: 1;
- pastas de scripts por projeto: 4;
- projetos com backup tecnico em `outputs/_project_scripts`: 8;
- arquivos operacionais `.py`, `.ps1` ou `.sql`: 98;
- scripts Python: 87;
- wrappers temporarios na raiz: 36;
- avisos organizacionais: 0.

## Validacoes executadas

- `python -m compileall scripts\projects scripts\migrations scripts\validation scripts\run scripts\maintenance scripts\prototypes scripts\_compat.py`
- `python -m compileall -l scripts`
- `python scripts\run\run_project_recipe.py geoher001_herculano_2022_2025 --env-file .env --dry-run`
- `python scripts\validation\check_repo_organization.py`

## Observacoes

- Os scripts movidos aparecem no Git como grandes reducoes na raiz porque a raiz
  passou a conter wrappers de compatibilidade.
- O codigo real foi preservado nas subpastas organizadas.
- O arquivo JSON mais recente do validador foi gerado em
  `outputs/_runs/repository_organization_latest.json`, que permanece como
  artefato local por regra de ignore de `outputs/`.
