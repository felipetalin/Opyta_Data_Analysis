# GEOHER001 Maintenance

Scripts pontuais usados na correcao e auditoria do projeto GEOHER001
`Monitoramento de ictio e bentos - Herculano`.

Estes arquivos sao historicos e nao devem ser usados como pipeline analitico
principal. Para gerar resultados definitivos, usar `scripts/run_pipeline.py`
com a receita em `configs/projects/geoher001_herculano_2022_2025.json`.

## Normalizacao taxonomica de Zoobentos

O script `normalize_geoher001_bentos_taxonomy.py` audita todas as campanhas do
projeto e aplica, com backup transacional, as seguintes regras:

- `Artropoda` deve ser normalizado para `Arthropoda`;
- `Insecta` e a classe; Coleoptera, Diptera, Ephemeroptera e demais grupos
  equivalentes devem ocupar o campo ordem;
- `Bivalvia` e a classe e `Veneroida` e a ordem;
- nomes de familia, como `Staphylinidae`, nao podem ser repetidos no campo
  genero;
- o campo genero recebe somente o nome do genero, sem o qualificador `sp.`.

Executar primeiro a auditoria e somente depois a aplicacao:

```powershell
python scripts\maintenance\geoher001\normalize_geoher001_bentos_taxonomy.py --env-file .env
python scripts\maintenance\geoher001\normalize_geoher001_bentos_taxonomy.py --env-file .env --apply
```

Em 2026-06-19 foram corrigidos 42 taxons. O backup foi preservado em
`public.backup_geoher001_bentos_taxonomy_20260619t173235z`.
