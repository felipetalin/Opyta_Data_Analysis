# ITAGUA001 - Ictiofauna - C029/2026

- estado atual: `configuring_analysis`
- aberta e atualizada em: 2026-09-08
- escopo autorizado: iniciar migracao apenas da campanha 29; nao gerar resultados.
- identidade: `ITAGUA001__monitoramento_da_fauna`, id_projeto 165 reconfirmado no Supabase nesta revalidacao; conexao restabelecida. Nenhum resultado de ictiofauna encontrado para campanhas com prefixo C029 no projeto.
- proxima acao: configurar e aprovar template, paleta, pasta e produtos no Gate C; nenhum produto foi gerado.

## Caminhos e dependencias consultadas

- fonte: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Campanhas de campo\29_campanha-Julho_26\Ictiofauna\3.Agosto-26\Planilha\projeto_ictio_real-Guanhães_260817.xlsx`
- saida futura informada: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\29_campanha_Jul_26`
- fonte original preservada; nenhuma carga ou geracao executada.
- validacao reproduzivel: `scripts/projects/itagua001/validate_ictio_c029.py`; evidencia: `ITAGUA001_ICTIOFAUNA_C029_VALIDATION.json` nesta pasta.
- migrador consultado: `G:/Meu Drive/Opyta/Opyta_Data/scripts/migrar_ictiofauna.py`, para verificar chaves, agregacao e abrangencia da limpeza.
- registry: somente entrada ITAGUA001; operacao irma: Herpetofauna C029; dossie: `docs/PIPELINE_ICTIO_165.md`; nenhuma recipe registrada.
- lastro informado pelo usuario localizado em `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna/ictiofauna`; somente nomes listados para localizar referencias, nenhum produto historico aberto.

## Validacao e pendencias concretas

- A fonte contem historico completo. O migrador atual limpa/recarrega todas as campanhas da fonte: nao executar diretamente sobre este arquivo. Preparar recorte exclusivo apos resolver Gate A.
- C029 na fonte: `C029-2026-08-SC`, data `2026-08-01`; manter agosto, embora pasta de saida seja julho.
- 32 pontos, 49 esforcos, 99 linhas de resultados, 235 individuos e 14 especies; agregacao prevista: 66 linhas antes dos ajustes.
- Sem duplicacao das chaves de pontos/esforcos, sem chaves de agrupamento vazias e sem valores numericos ausentes, negativos ou zero nos campos verificados (abundancia, CT, PC, esforco).
- 9 linhas / 15 individuos sem chave de esforco correspondente:
  - `RPJAC05`: 4 linhas / 6 individuos. Cadastro e esforco usam `RPJAC5`; proposta: normalizar codigo no recorte.
  - `RPSPT04`: 4 linhas / 6 individuos. Cadastro e esforco usam `RPSPT4`; proposta: normalizar codigo no recorte.
  - `TRDGN2`: 1 linha / 3 individuos de Phalloceros uai. Resultado indica Rede de emalhar / Quantitativa / malha 3 mm; esforco cadastrado indica Peneira e arrasto / Qualitativa. Confirmar metodo e tipo corretos antes de alterar.
- As quatro linhas de RPJAC05 e RPSPT04 repetem especies, abundancias, malhas e biometrias entre os dois pontos. Pode ser coincidencia ou copia; confirmar que sao capturas independentes.
- Coordenadas: 32 presentes, numericas e em faixa global valida; todas iguais a C028 da propria fonte. Isso nao equivale a validacao espacial externa.
- Coordenadas compartilhadas: RPJAC5/RPSPT4 e TRJAC4/TRSPT1/TRSPT2/TRSPT3. CRS e referencia espacial oficial nao informados. Confirmar referencia ou aceitar expressamente ressalva de uso das coordenadas da fonte; nenhuma correcao espacial inferida.
- Cadastro de especies nao consta como aba da fonte. Auditoria no banco e atributos pendentes apos Gate A.

## Gates

| Gate | Estado | Evidencia |
| --- | --- | --- |
| A | aprovado com ressalva espacial | Usuario confirmou Peneira e arrasto em TRDGN2 e autorizou coordenadas da planilha sem referencia externa; recorte revalidado sem chaves faltantes. |
| B | aprovado por preenchimento direto | Usuario informou os valores faltantes; 14/14 completos nos campos auditados e revalidados antes da carga. |
| C | fora do escopo | Usuario proibiu geracao de resultados nesta etapa. |

Migracao e consolidacao nao executadas. Nenhuma alteracao no banco ou na planilha original.

## Revalidacao apos ajustes do usuario - 2026-09-08

- Usuario informou normalizacao de RPJAC05/RPSPT04, ajuste de TRDGN2 para qualitativo e confirmou que capturas iguais entre os dois pontos sao legitimas.
- Fonte relida; SHA256 atual `3f8ca8ac99a2f3c7ba11d89b28dfd7969d638a6e05f257aa8a6b12951e90abc0`. Hash anterior `7b4ee551a35d586369f03eba7d6c92995eaaab4bd22ae61fb6736721777121cb` preservado aqui como linha de base.
- Normalizacao dos dois pontos confirmada: nenhuma chave faltante para RPJAC5/RPSPT4. Pendencia de capturas iguais encerrada pela confirmacao explicita do usuario.
- Totais mantidos: 99 linhas, 235 individuos, 14 especies, 32 pontos, 49 esforcos e 66 grupos de agregacao.
- Permanece uma chave faltante: TRDGN2 / Rede de emalhar, envolvendo 3 individuos. Alterar apenas Tipo_de_Amostragem nao resolve a chave Metodo_de_Captura. Confirmar metodo correspondente a Peneira e arrasto antes de preparar carga.
- Coordenadas inalteradas; referencia espacial/aceite da ressalva continua pendente, nao respondida nesta mensagem.
- Gate A permanece pendente apenas pelas questoes remanescentes; Gate B ainda nao iniciado. Nenhuma carga ou geracao realizada.

## Gate A concluido e auditoria do Gate B - 2026-09-08

- Autorizacao expressa do usuario: "confirmo que é peneira e arrasto" e "autorizo" manter coordenadas da fonte iguais a C028, sem referencia espacial externa.
- Ajuste aplicado somente ao recorte em memoria/JSON: linha-fonte 10872, TRDGN2, Metodo_de_Captura de Rede de emalhar para Peneira e arrasto; Tipo_de_Amostragem Qualitativa preservado. Planilha original inalterada.
- Recorte tecnico revisavel: `ITAGUA001_ICTIOFAUNA_C029_PREPARED.json` nesta pasta. Inclui hash da fonte, ajuste autorizado e numeros das linhas originais; nao e produto analitico.
- Revalidacao com `python scripts/projects/itagua001/validate_ictio_c029.py --approved-adjustments`: nenhuma chave faltante; 32 pontos, 49 esforcos, 99 linhas, 235 individuos, 14 especies e 66 agregados. Coordenadas mantidas pela estrategia `sem_referencia_externa_aprovada`, com ressalva explicitamente aceita.
- Identidade 165 reconfirmada; nenhuma ictiofauna C029 existente no banco.
- Auditoria local do cadastro: 14 correspondencias exatas e nenhum taxon novo. Endemismo ausente em 14/14; ameaca nacional/global ausentes em 6/14; origem presente em 14/14. Hoplias malabaricus e Rhamdia quelen possuem referencia estadual de MT, inadequada para validar MG.
- Evidencia revisavel: `ITAGUA001_ICTIOFAUNA_C029_TAXONOMY_REVIEW.md`; snapshot: `ITAGUA001_ICTIOFAUNA_C029_TAXONOMY.json`.
- Gate B nao pode ser marcado como cadastro completo. Proposta submetida: reutilizar cadastro existente exclusivamente na carga com ressalvas, complementando atributos antes de resultados, se expressamente aprovado; ou completar cadastro com fonte aprovada antes da carga.
- Dependencia tecnica adicional consultada: `G:/Meu Drive/Opyta/Opyta_Data/scripts/migrar_detalhes_reprodutivos_ictio.py`. O sincronizador remove detalhes do projeto inteiro; nao executar diretamente com recorte de campanha. Carga futura deve restringir detalhes a C029 e preservar historico em transacao.
- Nenhuma escrita no banco, consolidacao ou geracao de resultados executada.

## Gate B concluido e migracao executada - 2026-09-08

- Usuario forneceu diretamente ameaca/endemismo/origem pendentes e autorizou continuidade. Nenhuma fonte externa foi usada nos valores aplicados.
- Cadastro atualizado e revalidado: 14/14 especies localizadas; zero ausencias em `status_ameaca_nacional`, `status_ameaca_global`, `origem` e `endemismo`.
- `Delturus carinotus`: `Endêmica da bacia do rio Doce`; `Cichla kelberi`: `Não endêmica`, origem `Exótica na bacia do rio Doce; nativa da bacia Amazônica`; demais valores conforme informados pelo usuario.
- Auditoria antes/depois: `ITAGUA001_ICTIOFAUNA_C029_TAXONOMY_UPDATE.json`. Gate B aprovado pelo fornecimento expresso dos valores e revalidacao sem lacunas.
- Migracao transacional exclusiva de `C029-2026-08-SC` executada no projeto 165. O historico fora da C029 nao entrou no escopo de limpeza/escrita.
- Comparacao fonte x banco: 32 pontos e 49 esforcos carregados; 66 resultados agregados, 235 individuos e 14 especies. Destes, 20 pontos e 22 esforcos possuem resultados positivos.
- Detalhe da fonte preservado: 99 linhas e 235 individuos em `resultados_ictiofauna_detalhe`, restritos a C029.
- Evidencia: `ITAGUA001_ICTIOFAUNA_C029_MIGRATION.json`; executor: `scripts/projects/itagua001/migrate_ictio_c029.py`.
- Planilha original preservada; ajuste de TRDGN2 aplicado somente ao recorte autorizado. Nenhuma consolidacao ou geracao de resultados executada.

## Complementacao parcial do cadastro - 2026-09-08

- Usuario forneceu diretamente os valores; pesquisa externa interrompida conforme solicitado.
- Atualizacao executada em transacao e verificada para 14 especies. Valores anteriores e posteriores preservados em `ITAGUA001_ICTIOFAUNA_C029_TAXONOMY_UPDATE.json`.
- `status_ameaca_nacional`, `status_ameaca_global` e `status_estadual` definidos como `N.A.` para: Cichla kelberi, Delturus carinotus, Deuterodon taeniatus, Hypomasticus copelandii, Hypostomus affinis, Oreochromis niloticus, Hoplias malabaricus e Rhamdia quelen.
- `endemismo` definido como `Não endêmica` para: Astyanax lacustris, Geophagus brasiliensis, Hoplias intermedius, Hypomasticus thayeri, Knodus moenkhausii e Phalloceros uai.
- Revalidacao: 14/14 especies localizadas; nenhum vazio em ameaca nacional, ameaca global ou origem; referencias estaduais de MT eliminadas.
- Os oito endemismos restantes foram informados na mensagem seguinte e aplicados antes da migracao: sete `Não endêmica` e `Delturus carinotus` endemica da bacia do rio Doce.
- Gate B foi concluido apos a revalidacao dos 14 registros.

## Consolidacao concluida - 2026-09-08

- Preflight detectou 32 pontos C029 sem empreendimento; corrigidos por correspondencia exata de nome com os 32 pontos da C028. Todos receberam empreendimento e nenhum ficou ambiguo.
- `CP_cm` agregado estava ausente no migrador generico; 66 resultados foram preenchidos pela media ponderada por individuos das 99 linhas detalhadas antes da consolidacao.
- Backups transacionais restritos a C029: `bkp_itagua001_ictio_c029_20260908t162046z_pontos`, `_resultados`, `_detalhes` e `_consolidado`.
- Consolidado C029/Ictiofauna: 66 linhas, 235 individuos, 14 especies e 20 pontos com resultado; zero linhas sem empreendimento ou sem CP.
- Por empreendimento: Dores de Guanhaes 60 individuos/16 linhas; Fortuna II 63/14; Jacare 56/20; Senhora do Porto 56/16.
- Auditoria por tipo de amostragem confirmou 235 individuos: Dores 3 qualitativos + 57 quantitativos; Fortuna II 20 + 43; Jacare 56 quantitativos; Senhora do Porto 56 quantitativos.
- Evidencia: `ITAGUA001_ICTIOFAUNA_C029_CONSOLIDATION.json`; executor: `scripts/projects/itagua001/consolidate_ictio_c029.py`.
- Estado avancado para `configuring_analysis`. Gate C permanece pendente e nenhum resultado foi gerado.
