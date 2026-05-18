# README - Analises de Meio Fisico (Fisicoquimico)

## Objetivo
Este documento registra a arquitetura, estrutura operacional, padroes tecnicos e regras de execucao para as analises de Meio Fisico no Opyta Data Analysis.

Escopo atual:
- Pipeline de diagnostico para dados fisicoquimicos consolidados.
- Execucao por matriz ambiental.
- Suporte a projetos com codigo interno Opyta.

## Arquitetura Funcional

### Pipeline principal
- Modulo: `src/opyta_analysis/pipelines/diagnostico/meio_fisico.py`
- Funcao publica: `run_meio_fisico_pipeline(...)`
- Dispatcher do runner: `src/opyta_analysis/runner.py`
- Aliases suportados no runner:
  - `meio_fisico`
  - `fisico`
  - `meio-fisico`
  - `physicochemical`

### Fonte de dados
- Tabela: `public.fisico_analise_consolidada`
- Tipo: tabela desnormalizada (nao e view)
- Filtro por projeto: `codigo_interno_opyta` (texto)
- Conexao: SQLAlchemy via variavel de ambiente `FISICO_DB_URL`

### Diferenca para pipelines de biota
- Biota usa Supabase REST + tabelas normalizadas por grupo.
- Meio Fisico usa SQL direto no Postgres consolidado via SQLAlchemy.
- Chave operacional do meio fisico no runner: `params.client.upper()`.

## Estrutura de Saida
Saida por matriz dentro do diretorio informado em `--output-dir`:

- `<output_dir>/<matriz_sanitizada>/01_Conformidade.xlsx`
- `<output_dir>/<matriz_sanitizada>/02_Violacao_Parametro_Campanha.png`
- `<output_dir>/<matriz_sanitizada>/03_Series_Temporais_*.png`
- `<output_dir>/<matriz_sanitizada>/04_IQA_IGAM.png` (agua superficial)
- `<output_dir>/<matriz_sanitizada>/05_IET_Lamparelli.png` (agua superficial)
- `<output_dir>/<matriz_sanitizada>/06_IQASB.png` (agua subterranea)
- `<output_dir>/<matriz_sanitizada>/07_mPELq.png` (sedimento)

## Blocos Analiticos

### Bloco 01 - Conformidade (Excel)
- Tabela parametro x campanha/ponto.
- Celulas em vermelho para violacoes de VMP.

### Bloco 02 - Percentual de violacao
- Grafico de barras por parametro e campanha.
- Baseado na funcao central de violacao.

### Bloco 03 - Series temporais
- Series por parametro ao longo das campanhas.
- Linhas de referencia de VMP e faixa visual quando aplicavel.

### Bloco 04 - IQA (IGAM)
- Aplicavel somente para Agua Superficial.
- Calcula indice composto conforme metodologia implementada no pipeline.

### Bloco 05 - IET (Lamparelli 2004)
- Aplicavel somente para Agua Superficial.
- Indicador de estado trofico.

### Bloco 06 - IQASB (ABAS)
- Aplicavel somente para Agua Subterranea.

### Bloco 07 - m-PEL-q (CETESB)
- Aplicavel somente para Sedimento.
- Indicador de potencial toxicidade sedimentar.

## Regras de Negocio e Normalizacao
- Campanhas suportam dois padroes:
  - legado: `mes-ano` (ex.: `jan-2021`)
  - novo: `CNNN-YYYY-MM-SC|CH` (ex.: `C028-2026-04-SC`)
- Ordenacao de campanha e feita por parser dedicado.
- `sinal_limite = '<'` indica valor abaixo de deteccao:
  - regra analitica adotada: usar `valor_medido/2` nos calculos que exigem numerico.

## Padrao Visual Gold - Parametrizacao de Cores
- Cores tecnicas de classificacao e limites do Meio Fisico estao parametrizadas no tema.
- Chaves prefixadas com `mf_` em:
  - `configs/theme_gold_approved.json`
  - `configs/theme_default.json`
- Exemplos de grupos de chave:
  - `mf_violation_palette` (bloco 02)
  - `mf_vmp_*` (linhas e sombra de VMP no bloco 03)
  - `mf_iqa_*`, `mf_iet_*`, `mf_iqasb_*`, `mf_mpelq_*` (faixas por classe)
  - `mf_marker_color` (marcadores dos indices)

## Colunas Criticas de VMP
Campos utilizados na avaliacao de conformidade:
- `vmp_357_cl1_min`, `vmp_357_cl1_max`
- `vmp_357_cl2_min`, `vmp_357_cl2_max`
- `vmp_amonia_dinamico`
- `vmp_454_n1`, `vmp_454_n2`
- `vmp_396_consumo_humano`
- `vmp_396_dessedentacao_animal`
- `vmp_396_irrigacao`
- `vmp_396_recreacao`
- `vmp_430_padrao`

## Configuracao de Ambiente
No arquivo `.env` usado na execucao, incluir:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `FISICO_DB_URL`  (obrigatorio para meio fisico)

## Execucao

### Exemplo de execucao geral
```bash
python scripts/run_pipeline.py \
  --project-id 115 \
  --group MeioFisico \
  --pipeline meio_fisico \
  --client braang01 \
  --output-dir "G:/Meu Drive/.../Resultados/Meio_Fisico" \
  --env-file "G:/Meu Drive/Opyta/Opyta_Data/.env" \
  --block all
```

Observacoes:
- O `project_id` e mantido por compatibilidade do runner.
- A consulta do meio fisico usa `client` para derivar `codigo_interno_opyta`.

## Migracao de Dados (SAM Metais)
Script dedicado:
- `scripts/migrar_meio_fisico_sam.py`
- `scripts/validar_meio_fisico_sam.py` (pre-migracao obrigatoria)

Arquivos esperados:
- `Resultados_Meio_Fisico.xlsx`
- `cadastro_parametros_opyta.xlsx`

Fluxo recomendado:
1. Atualizar planilhas de migracao.
2. Rodar validacao dedicada:
  - `python scripts/validar_meio_fisico_sam.py`
3. Inserir no banco:
   - `python scripts/migrar_meio_fisico_sam.py`
4. Reprocessar pipeline com `--client fersam001`.

Comportamento de seguranca na migracao:
- `migrar_meio_fisico_sam.py` executa validacao automaticamente antes de inserir.
- Se houver erro de validacao, a migracao e bloqueada.
- Flags de excecao (uso controlado):
  - `--skip-validation`
  - `--allow-validation-errors`

## Estado Atual Conhecido
- BRAANG01: dados presentes e utilizaveis para teste de pipeline.
- FERSAM001: sem registros na tabela consolidada ate concluir migracao.
- Matrizes SAM previstas: Agua Superficial, Agua Subterranea, Sedimento.

## Checklist Operacional
Antes de executar:
- Confirmar `FISICO_DB_URL` no `.env`.
- Confirmar `--client` correto.
- Confirmar pasta de saida final do cliente.
- Validar se a tabela possui dados para o codigo interno.

Depois de executar:
- Conferir blocos gerados por matriz.
- Revisar indicadores que nao se aplicam por tipo de matriz.
- Registrar evidencias no journal de projeto.

## Armadilhas Conhecidas
- Nao usar apenas `project_id` para meio fisico.
- Nao usar Supabase REST para consultas principais do consolidado.
- Nomes de campanha sem parser podem ficar fora de ordem.
- Valores com `<` sem tratamento distorcem indices.
- Migracao sem mapear VMP invalida bloco de conformidade.

## Referencias Internas
- `src/opyta_analysis/pipelines/diagnostico/meio_fisico.py`
- `src/opyta_analysis/runner.py`
- `src/opyta_analysis/pipelines/diagnostico/__init__.py`
- `src/opyta_analysis/pipelines/__init__.py`
- `scripts/migrar_meio_fisico_sam.py`
- `logs/PROJECT_JOURNAL.md`
