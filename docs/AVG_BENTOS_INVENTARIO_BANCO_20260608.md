# AVG Bentos - Inventario do Banco

Data do levantamento: 2026-06-08

## Escopo

- Projeto: `id_projeto = 9`
- Codigo interno: `BRAAVG002`
- Nome no banco: `Monitoramento de ictio e bentos - Brumado - AVG`
- Grupo alvo: `Zoobentos`

## Situacao Atual

A migracao e a consolidacao de Bentos foram aplicadas em 2026-06-08 a partir
da planilha revisada:

`G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos\Planilha Consolidada\Migração de dados\2026\Bentos\projeto_bentos_real - AVG- 260608 - Rev.xlsx`

Na tabela fisica `biota_analise_consolidada`, para `BRAAVG002`:

| grupo_biologico | linhas | campanhas | pontos | taxons | contagem_total | primeira_coleta | ultima_coleta |
|---|---:|---:|---:|---:|---:|---|---|
| Zoobentos | 3876 | 44 | 13 | 116 | 12358 | 2022-08-01 | 2026-03-01 |

Nas tabelas base:

- `pontos_coleta`: 46 campanhas cadastradas para o projeto, com 13 pontos por campanha.
- `esforcos_amostragem`: `Ictiofauna` possui 598 esforcos distintos, isto e, 46 x 13.
- `esforcos_amostragem`: `Zoobentos` possui 572 esforcos distintos, isto e, 44 x 13.
- `resultados_zoobentos`: 3876 resultados para o projeto AVG.
- Esforcos de Zoobentos com resultado: 533.
- Especies/taxons distintos em resultados de Zoobentos: 116.
- Abundancia total em `resultados_zoobentos`: 12358.

## Campanhas Mais Recentes

| id_campanha | campanha | pontos | data_hora_coleta no banco | esforcos ictio | esforcos zoobentos | resultados zoobentos |
|---:|---|---:|---|---:|---:|---:|
| 116 | `42a-Jan-26` | 13 | 2026-01-01 | 13 | 13 | 43 |
| 117 | `43a-Fev-26` | 13 | 2026-02-01 | 13 | 13 | 68 |
| 495 | `44a-Mar-26` | 13 | 2026-03-01 | 13 | 13 | 40 |
| 496 | `45a-Abr-26` | 13 | 2026-02-01 | 13 | 0 | 0 |
| 497 | `46a-Mai-26` | 13 | 2026-03-01 | 13 | 0 | 0 |

Observacao sobre rotulos: o banco usa os nomes com simbolo ordinal feminino
real. Este documento usa a forma ASCII (`45a`, `46a`) apenas para evitar ruido
de codificacao em terminais/console. A chave operacional segura para migracao
deve ser `id_campanha`.

Atencao: `45a-Abr-26` esta com `data_hora_coleta = 2026-02-01` e
`46a-Mai-26` esta com `data_hora_coleta = 2026-03-01` nos pontos cadastrados.
Antes de migrar Bentos para abril/maio, confirmar se essas datas devem ser
corrigidas ou mantidas para consistencia com a carga de Ictiofauna.

## Aprendizado Ictio: Ordinal vs Letra

No runner AVG de Ictiofauna, o problema `46a` versus simbolo ordinal feminino
foi resolvido por canonizacao: o texto da campanha e normalizado, variantes de
ordinal sao convertidas, mes/ano sao extraidos e a saida volta para o padrao
canonico do AVG.

Esse tratamento esta em `scripts/run_ictio_avg_abril_maio.py`, funcao
`canonical_campaign`.

Para Bentos, o pipeline generico atual nao tem essa canonizacao; ele apenas
carrega `nome_campanha` a partir de `id_campanha` dos pontos e faz `strip()`.
Portanto:

1. Se a carga de Bentos usar os pontos existentes por `id_campanha`, nao ha
   problema de `46a` versus ordinal.
2. Se a carga buscar campanha por texto literal, ha risco de falha ou duplicata.
3. A migracao de Bentos deve resolver os alvos assim:
   - `43a-Fev-26` -> `id_campanha = 117`
   - `44a-Mar-26` -> `id_campanha = 495`
   - `45a-Abr-26` -> `id_campanha = 496`
   - `46a-Mai-26` -> `id_campanha = 497`

Consulta feita em 2026-06-08: nao ha duplicidades normalizadas dessas campanhas
no projeto 9; cada campanha alvo existe uma unica vez.

## Pontos Sem Resultado de Zoobentos

Historicamente ha campanhas com 13 esforcos de Zoobentos, mas menos de 13 pontos
com resultado. Isso pode representar captura zero, ausencia real de resultado ou
lacuna de migracao, dependendo da planilha fonte.

Campanhas recentes:

- `42a-Jan-26`: sem resultado em `PIC-01`, `PIC-02`, `PIC-03`, `PIC-11`.
- `43a-Fev-26`: esforco em 13 pontos; sem resultado em `PIC-01`, `PIC-11`.
- `44a-Mar-26`: esforco em 13 pontos; sem resultado em `PIC-01`, `PIC-03`, `PIC-11`.
- `45a-Abr-26`: sem esforcos/resultados de Zoobentos em todos os 13 pontos.
- `46a-Mai-26`: sem esforcos/resultados de Zoobentos em todos os 13 pontos.

## Qualidade Taxonomica

Nos 3876 resultados atuais de Zoobentos:

- `id_especie` ausente: 0
- `id_especie` sem cadastro em `especies`: 0
- `nome_cientifico` ausente: 0
- `ordem` ausente: 115 linhas
- `familia` ausente: 125 linhas
- `bmwp_score` ausente: 774 linhas

Taxons mais abundantes no historico:

| taxon | abundancia_total | registros |
|---|---:|---:|
| `Chironomidae` | 4811 | 459 |
| `Simuliidae` | 1365 | 194 |
| `Tipulidae` | 778 | 268 |
| `Ceratopogonidae` | 633 | 245 |
| `Elmidae` | 484 | 217 |
| `Veliidae` | 364 | 151 |
| `Sphaerium sp.` | 240 | 91 |
| `Gomphidae` | 230 | 110 |
| `Oligochaeta` | 190 | 101 |
| `Smicridea sp.` | 162 | 58 |

## Registro da Migracao Executada

1. A validacao oficial do Opyta Data aprovou a planilha revisada: 44 campanhas,
   572 pontos e 3896 registros, sem bloqueios e sem especies desconhecidas.
2. A migracao substituiu a fatia AVG/Zoobentos nas tabelas base: 572 pontos,
   572 esforcos preparados e 3876 resultados agregados.
3. A consolidacao substituiu somente `codigo_interno_opyta = 'BRAAVG002'` e
   `grupo_biologico = 'Zoobentos'` em `biota_analise_consolidada`.
4. A fatia antiga consolidada foi preservada em
   `bkp_biota_avg_zoobentos_20260608_112425`.
5. Auditorias geradas em `outputs/_migration/avg_bentos_2026/`:
   `migration_applied.json` e `consolidation_applied.json`.
6. Nao foram executadas analises ecologicas nesta etapa.

## Registro dos Resultados Fev/Mar 2026

Rodada final executada em 2026-06-08 com o script dedicado
`scripts/run_bentos_avg_2026_por_campanha.py`, filtrando exclusivamente as
campanhas:

- `43a-Fev-26`, saida em
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos\Planilha Consolidada\Resultados e planilhas\Resultados bentos\2026\Fevereir-26`
- `44a-Mar-26`, saida em
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos\Planilha Consolidada\Resultados e planilhas\Resultados bentos\2026\marco-26`

Resumo validado:

| pasta | campanha no banco | registros | pontos com resultado | taxons | abundancia_total | arquivos |
|---|---|---:|---:|---:|---:|---|
| `Fevereir-26` | `43a-Fev-26` | 68 | 11 | 25 | 218 | 14 xlsx, 11 png, 1 json |
| `marco-26` | `44a-Mar-26` | 40 | 10 | 16 | 154 | 14 xlsx, 11 png, 1 json |

Ajustes finais aplicados aos graficos:

1. Graficos `06B` e `06C` usam paleta verde contrastante iniciada pela cor
   primaria do tema AVG.
2. Grafico de rosca `05` usa a mesma paleta verde dos graficos `06B` e `06C`
   para preservar a identidade visual.
3. Grafico `02` foi gerado sem legenda.
4. O falso taxon `Nao informado` foi removido dos produtos; quando `ordem`
   esta ausente, o pipeline usa o menor nivel taxonomico disponivel
   (`taxon_final`, `familia`, `classe` ou `filo`).

Validacoes finais:

- `python -m py_compile` aprovado para o pipeline e os scripts de Bentos.
- Regeneracao das duas campanhas executada sem erro.
- Conferencia dos arquivos de saida sem ocorrencia de `Nao informado`.
- PNGs conferidos como nao vazios.
- Spot-check visual dos graficos `02` e `05` aprovado.

## Pipeline Disponivel

Existe pipeline generico para Zoobentos:

```powershell
python scripts/run_pipeline.py `
  --project-id 9 `
  --group Zoobentos `
  --pipeline zoobentos `
  --client braavg002 `
  --output-dir "<pasta de resultados AVG Bentos>" `
  --env-file "G:\Meu Drive\Opyta\Opyta_Data\.env" `
  --block all `
  --audit-project-slug avg_bentos_2026
```

Observacao: `configs/clients/braavg002.json` ainda usa
`audit_project_slug = avg_ictio_2026`. Para Bentos, usar
`--audit-project-slug avg_bentos_2026` ou criar um ajuste dedicado antes da
execucao oficial.
