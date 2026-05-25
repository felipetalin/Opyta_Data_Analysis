# Meio Físico — SAM Metais (FERSAM001)

Snapshot rastreável dos scripts e configuração que geraram os outputs aprovados em **Gold v1** (`gold-meio-fisico-v1`, commit `b92c6df`) com fixes posteriores até **2026-05-25**.

## Como reproduzir
```powershell
cd "G:\Meu Drive\Opyta\Opyta_Data_Analysis"
$env:PYTHONPATH = (Resolve-Path "src").Path
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -c "from opyta_analysis.pipelines import run_meio_fisico_xlsx_pipeline; r = run_meio_fisico_xlsx_pipeline(client='FERSAM001', block='all'); print('FAILED:', r['failed_blocks']); print('N_FILES:', len(r['generated_files']))"
```
Esperado: `FAILED: []`, `N_FILES: 106`.

Validação pontual registrada em **2026-05-25**: blocos `b2`, `b4`, `b11` e `resumo` executados sem falha após correção da regra de violação em Água Superficial. Quando arquivos oficiais estavam bloqueados pelo Excel/Drive, os scripts salvaram versões `_NEW` e os blocos dependentes passaram a priorizar a versão mais recente.

## Estrutura
- `scripts_snapshot/` — cópia versionada (com prefixo `YYYYMMDDTHHMMSSZ_`) dos scripts `gerar_*.py`, do runner `meio_fisico_xlsx.py` e do config `fersam001.json` no momento do snapshot. Também guarda o arquivo "latest" sem prefixo.
- `scripts_snapshot/execution_metadata.json` — metadados da última execução validada (commit git, blocos executados, n_files, fixes recentes).
- `01_Conformidade_*.xlsx` e `03_ST_*.png` — outputs históricos (apenas amostras de validação Gold; outputs vivos ficam em `Produtos/Resultados/Meio_físico/` no Drive do cliente).

## Pipeline (10 blocos)
| Bloco | Script | Saída |
|-------|--------|-------|
| b2 | `gerar_conformidade_sam_etapa2.py` | `01_Conformidade_<matriz>.xlsx` (+ aba `Conversoes_Unidade`) |
| b3 | `gerar_b3_grafico_por_parametro.py` | `03_<parametro>.png` (somente VMPs) |
| b4 | `gerar_b4_pct_violacao.py` | `04_Pct_Violacao.png` + `.xlsx` |
| b5 | `gerar_b5_iqa_cetesb.py` | IQA CETESB (Superficial) |
| b6 | `gerar_b6_iet_lamparelli.py` | IET Lamparelli (Superficial) |
| b7 | `gerar_b7_iqasb_parcial.py` | IQASB parcial (Subterrânea) |
| b8 | `gerar_b8_mpelq.py` | MPELQ (Sedimentos) |
| b9 | `gerar_b9_sazonal.py` | `09_Sazonal_Boxplots_top12.png` + Mann-Whitney xlsx |
| b11 | `gerar_b11_sintese.py` | `11_Sintese_Executiva.xlsx` |
| resumo | `gerar_resumo_tecnico.py` | `RESUMO_<matriz>.txt` + `RESUMO_CONSOLIDADO.txt` |

## Regras Gold (resumo executivo)
- **Unidade dos dados é autoritativa** (moda da coluna `Unidade_Medida`). VMPs do cadastro são convertidos via `_conv_factor(unidade_cad, unidade_dados)` antes de violação e antes de plotar.
- Filtrar `VMP <= 0` e `VMP None`.
- b3: apenas linhas de VMP (CONAMA 396/357), sem LQ.
- Superficial usa **CONAMA 357 Classe 2** como referência operacional de conformidade do diagnóstico.
- b2: a marcação vermelha em Superficial deve usar apenas `VMP_357_Cl2_Min`, `VMP_357_Cl2_Max` e amônia dinâmica por pH.
- b4: `drop_duplicates(subset=["Parametro"], keep="first")` no cadastro como proteção defensiva; em Superficial deve avaliar limite mínimo e máximo, não apenas máximo.
- Caracteres `µ` (U+00B5) e `μ` (U+03BC) ambos normalizados.

## Fixes pós-Gold (2026-05-19)
1. **b4 conversão de unidade + filtro VMP<=0** (commit `e00701c`) — corrigiu Clorofila A 100% falsa em Superficial e violações infladas em Subterrânea.
2. **Cadastro Subterrânea corrigido na fonte** — 4 linhas (Nitrato, Cobre Total, Cloretos, Alumínio Total) estavam rotuladas `mg/L` mas valores eram µg/L. Patch openpyxl direto em `cadastro_parametros_opyta.xlsx`. Revelou Alumínio Total 12.5% em Subterrânea (antes mascarado).

## Fixes pós-Gold (2026-05-25)
1. **b4 Classe 2 min/max em Superficial** — `04_Pct_Violacao.xlsx` agora grava `Limite_Min`, `Limite_Max` e `Regra_VMP`; OD passa a ser contabilizado por violar o mínimo de 5 mg/L. Resultado validado: 8 parâmetros violados em Superficial (FE, CF, PH, AL, P, EC, OD, MN).
2. **b2 alinhado ao b3/b4** — `01_Conformidade_Agua_Superficial.xlsx` deixou de marcar qualquer classe e passou a marcar a referência operacional Classe 2. Isso remove falsos alertas como Turbidez por Classe 1.
3. **Resiliência a arquivo bloqueado** — `b4` avisa quando salva `_NEW`; `b11` e `resumo` leem a versão mais recente entre o arquivo oficial e `_NEW`.

## Sinal de alerta (para futuras revisões de cadastro)
> **VMP absurdamente grande** + **linhas duplicadas no cadastro** ≈ unidade trocada. Conferir antes de propagar.
> **Parâmetros com limite mínimo** (OD, pH/faixa) exigem regra `valor < limite_min`; se o script usa apenas `valor > VMP_ref`, a violação some silenciosamente.

## Referência de memória
- `/memories/repo/meio_fisico_gold_v1.md` — versão completa das regras Gold e armadilhas.
- `docs/MEIO_FISICO_MEMORIA_GOLD.md` — cópia versionada da memória operacional.
