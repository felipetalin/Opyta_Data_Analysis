# Fauna - auditoria operacional

Este documento registra o padrao minimo de lastro para os pipelines de fauna.
Ele segue a mesma intencao operacional adotada em `meio_fisico`: cada entrega
deve ser reproduzivel, conferivel e ligada ao estado do codigo usado.

## Escopo

Auditoria aplicavel aos grupos:

- Zoobentos
- Fitoplancton
- Zooplancton
- Ictiofauna
- Mastofauna
- Primatas
- Herpetofauna
- Avifauna
- Macrofitas

## Comando

Auditar um projeto especifico:

```bash
python scripts/validar_fauna_outputs.py --project sam_metais
```

Auditar todos os projetos com memorias em `outputs/_project_scripts`:

```bash
python scripts/validar_fauna_outputs.py
```

O manifesto padrao por projeto e gravado em:

```text
outputs/_project_scripts/<projeto>/fauna_inventory.json
```

O nome do projeto pode ser definido no arquivo do cliente com
`audit_project_slug`. Para `fersam001`, o lastro oficial usa `sam_metais`.

## O que a auditoria confere

- existencia do `execution_metadata.json` por grupo;
- existencia do `output_dir` declarado;
- consistencia entre `generated_files_count` e `generated_files`;
- existencia dos arquivos listados em `generated_files`;
- hash SHA-256, tamanho e data de modificacao dos arquivos de saida;
- presenca de `rows_loaded`, `executed_blocks`, contexto git e hashes gerados pelo runner;
- inventario de artefatos encontrados no diretorio de entrega.

## Aliases conhecidos

Algumas memorias antigas usam nomes formais de grupo enquanto a pasta de
entrega usa nome curto. A auditoria preserva o caminho declarado e registra
`output_dir_resolved_by_alias` quando encontra a pasta equivalente.

- `Fitoplancton` pode resolver para `Fito`
- `Zoobentos` pode resolver para `Bentos`
- `Ictiofauna` pode resolver para `Ictio`

## Aprendizado incorporado

O caso de fauna mostrou que saidas podem existir no Drive sem que a memoria
tecnica esteja completa. Por isso, a auditoria diferencia:

- `ERROR`: problema que impede confiar no lastro, como diretorio de saida ausente
  ou arquivo declarado que nao existe;
- `OK_WITH_WARNINGS`: entrega localizavel, mas com memoria incompleta ou antiga;
- `OK`: memoria, saidas e hashes coerentes.

## Regra para novas execucoes

Toda nova execucao via `scripts/run_pipeline.py` passa a registrar no
`execution_metadata.json`:

- versao do runner;
- branch, commit e dirty status do git;
- lista de arquivos gerados;
- hash SHA-256 e tamanho de cada arquivo gerado;
- alerta se algum arquivo declarado estiver ausente.

Antes de fechar uma entrega de fauna, rode a auditoria e anexe o
`fauna_inventory.json` ao lastro tecnico do projeto.
