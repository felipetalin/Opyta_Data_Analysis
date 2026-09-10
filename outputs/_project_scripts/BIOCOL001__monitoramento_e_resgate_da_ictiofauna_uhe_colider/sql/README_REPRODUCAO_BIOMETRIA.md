# BIOCOL001 - proposta tecnica para sexo/EMG/biometria

## Diagnostico

- A planilha-fonte de BIOCOL001 possui dados reprodutivos relevantes:
  - `CP_cm`: 71.202 linhas de 74.589, 95,46%;
  - `PC_g`: 74.570 linhas de 74.589, 99,97%;
  - `Sexo`: 13.513 linhas de 74.589, 18,12%;
  - `EMG`: 13.439 linhas de 74.589, 18,02%.
- A tabela `public.resultados_ictiofauna` possui colunas `cp_cm`, `sexo` e `emg`, mas o script atual de migracao agregou por `Campanha + Ponto + Metodo_de_Captura + Nome_Cientifico` e gravou apenas `ct_cm` e `pc_g`.
- A constraint `uq_resultado_ictio_por_esforco_especie` impede mais de uma linha por `id_esforco + id_especie`.
- Na fonte BIOCOL001 existem grupos agregados com informacao heterogenea:
  - 1.408 grupos `Campanha + Ponto + Metodo + Especie` com mais de um sexo;
  - 995 grupos com mais de um EMG.

## Conclusao

Nao e tecnicamente correto preencher `sexo` e `emg` diretamente na tabela agregada
`resultados_ictiofauna` quando houver mais de um valor no mesmo resultado agregado.
Para o banco definitivo, a informacao reprodutiva deve ficar em tabela detalhe,
preservando a granularidade da planilha-fonte.

## Referencia BIOPOR001

Em Porto Estrela, `Sexo` e `EMG` foram usados com sucesso na base analitica
derivada da planilha validada, com padronizacao para:

- `Sexo_Padronizado`;
- `EMG_Codigo`;
- `EMG_Estadio`;
- `EMG_Ordem`;
- `Evidencia_Reprodutiva_Forte`.

O banco de BIOPOR001 tambem nao ficou com `sexo`/`emg` preenchidos em
`resultados_ictiofauna`, portanto BIOCOL001 deve evoluir o modelo antes da
geracao definitiva do tema 5.12.

## Caminho recomendado

1. Criar tabela complementar de detalhe, por linha/individuo-lote da planilha:
   `public.resultados_ictiofauna_detalhe`.
2. Vincular cada detalhe ao resultado agregado por `id_resultado_ictio`.
3. Preservar valores brutos e valores padronizados:
   `sexo_raw`, `sexo_padronizado`, `emg_raw`, `emg_codigo`, `emg_estadio`,
   `emg_ordem`, `evidencia_reprodutiva_forte`.
4. Reprocessar BIOCOL001 a partir da planilha v3 para carregar os detalhes.
5. Replicar depois para BIOPOR001, se desejado, para harmonizar o banco historico.

