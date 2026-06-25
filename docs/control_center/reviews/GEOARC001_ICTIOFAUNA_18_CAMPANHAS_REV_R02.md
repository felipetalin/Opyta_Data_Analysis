# GEOARC001 - Ictiofauna - 18 campanhas - Revisao R02

## Controle

- projeto: GEOARC001__monitoramento_arcelor
- operacao de origem: docs/control_center/operations/GEOARC001_ICTIOFAUNA_18_CAMPANHAS.md
- revisao: R02
- estado atual: awaiting_revision_approval
- solicitada em: 2026-06-23
- atualizada em: 2026-06-23
- proxima acao: usuario aprovar ou solicitar novo ajuste no Gate R

## Escopo

- solicitacao do usuario: organizar e validar a saida final de Ictiofauna; corrigir graficos com rotulos do eixo X sobrepostos; melhorar HTML textual
- tipo principal: text
- tipos secundarios: layout, analysis, package
- impacto: R2
- justificativa do impacto: correcao de numeros derivados na narrativa/HTML, sem alteracao de banco, migracao, consolidacao ou planilhas-fonte
- produtos alvo: pacote final em `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Resultados/Ictiofauna`
- fora do escopo: alteracoes de dados brutos, taxonomia aprovada, scripts oficiais de migracao/consolidacao e registros no banco

## Linha De Base

- pasta/arquivo: pasta final GEOARC001/Ictiofauna indicada pelo usuario
- snapshot/backup: `outputs/_reviews/geoarc001_ictiofauna_R01/baseline/20260623_202936`
- auditoria inicial R02:
  - `outputs/_reviews/geoarc001_ictiofauna_R02/html_audit_baseline.json`
  - `outputs/_reviews/geoarc001_ictiofauna_R02/numeric_audit_baseline.json`
  - `outputs/_reviews/geoarc001_ictiofauna_R02/visual_contact_sheet_baseline.jpg`

## Dependencias E Retorno

- Gate A reaberto: nao
- Gate B reaberto: nao
- Gate C reaberto: sim, apenas para produtos de analise, layout e relatorio
- banco afetado: nao
- migracao/consolidacao afetadas: nao
- produtos dependentes: figuras, HTML, evidencias, validacao textual e manifesto

## Achados

| Achado | Impacto | Acao |
| --- | --- | --- |
| HTML com pouca narrativa visivel | leitura tecnica insuficiente | ampliada narrativa e adicionada secao de composicao |
| HTML citava GEOHER001 como referencia do projeto | lastro incorreto | referencia alterada para `docs/projects/GEOARC001_ARCELOR_ICTIOFAUNA.md` |
| Origem taxonomica no texto podia contar `Nao Nativo` como `Nativo` | numero derivado incorreto no HTML | normalizacao textual corrigida: 21 nativos e 2 nao nativos |
| Ranking por especie usava primeira campanha da planilha, nao acumulado da serie | sintese quantitativa incorreta | ranking por especie corrigido para soma das 18 campanhas |
| Bray-Curtis no texto usava a primeira comparacao da matriz | sintese de similaridade incorreta | calculada media do triangulo superior da matriz, sem diagonal |
| Rotulos C01-C18 comprimidos em paineis pequenos | sobreposicao visual | figuras 02 e 03 passaram a mostrar todas as campanhas com rotulos perpendiculares em 10 pt e eixo Y unico por painel composto |
| HTML exibia apenas os paineis de CPUE de 2022 | pacote incompleto no relatorio | incluidos todos os paineis anuais 2022-2026 para CPUEn e CPUEb |
| Rotulos de familia/ordem desalinhados com marcas do eixo X | desalinhamento visual | rotulos dos graficos de barras foram ancorados ao tick correspondente |
| Texto visivel continha termos sem acento em titulos/eixos | qualidade textual | corrigidos termos como numero, familia, especie, indice, media e abundancia nos produtos graficos/textuais |
| Figura 07 com nomes de pontos sobrepostos | sobreposicao visual | nomes dos pontos mantidos perpendiculares e com fonte reduzida nos paineis anuais |
| Figura 04C com pontos amostrais sobrepostos no eixo X | sobreposicao visual | pontos amostrais rotacionados para 90 graus no heatmap de frequencia de ocorrencia por ponto |
| Figura 08 precisava de leitura por ponto amostral | novo produto analitico | gerada figura/planilha `08B` de CPUEn por especie e ponto amostral |
| Figura 09 precisava de leitura por ponto amostral | novo produto analitico | gerada figura/planilha `09B` de CPUEb por especie e ponto amostral |
| Tabela 01 de composicao estava resumida | produto incompleto | tabela expandida para 35 colunas, incluindo autoria, atributos ecologicos, status, ocorrencia por campanhas/pontos e abundancia total |

## Arquivos Regenerados

- `relatorio_tecnico_ictiofauna_geoarc001.html`
- `evidencias_relatorio_ictiofauna_geoarc001.json`
- `validacao_textual_ictiofauna_geoarc001.json`
- `manifesto_entrega_ictiofauna_geoarc001.json`
- figuras PNG e planilhas XLSX do pipeline `ictio` nos blocos afetados

## Validacao Pos-Revisao

- validacao textual: `OK`, 0 erros, 0 avisos
- HTML: 34 paragrafos, 585 palavras em paragrafos, 26 figuras, 0 mencoes a GEOHER001
- tabela 01: 23 especies, 35 colunas, 23 autores preenchidos
- numeros-chave:
  - campanhas: 18
  - pontos no produto analitico: 11
  - pontos com captura: 9
  - taxa: 23
  - individuos: 707
  - origem: 21 nativos e 2 nao nativos
  - Bray-Curtis, similaridade media entre pares: 16,18%
- auditoria final: `outputs/_reviews/geoarc001_ictiofauna_R02/final_audit.json`
- prancha visual final: `outputs/_reviews/geoarc001_ictiofauna_R02/visual_contact_sheet_final.jpg`

## Gate R

- status: awaiting_user_approval
- comparacao antes/depois:
  - HTML saiu de 12 para 26 figuras
  - HTML saiu de 294 para 585 palavras em paragrafos
  - referencias GEOHER001 foram removidas do pacote textual
  - rotulos de campanha em paineis longos ficaram completos, perpendiculares e em 10 pt
  - figura 04C recebeu pontos amostrais perpendiculares no eixo X
  - figura 08B foi adicionada para CPUEn por especie e ponto amostral
  - figura 09B foi adicionada para CPUEb por especie e ponto amostral
  - tabela 01 foi ampliada com dados taxonomicos, autor e ano, atributos ecologicos e lastro de ocorrencia
  - sinteses textuais de origem, especies dominantes e Bray-Curtis foram corrigidas

## Pendencias

- aguardar aprovacao do usuario para fechar a R02 como `review_completed`
