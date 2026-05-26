# Auditoria arquitetura fauna - execucao multiuso

Data: 2026-05-26

## Escopo

Auditoria dos scripts atuais de fauna para preparar a migracao da Avifauna e
reduzir scripts especificos por projeto/campanha. O foco operacional imediato e
Itatiaia/Guanhaes Energia, campanha `C028-2026-05-SC`, mas a arquitetura deve
servir para campanhas futuras e outros projetos.

Arquivos avaliados:

- `scripts/run_ictio_partial_multi_empreendimentos.py`
- `scripts/run_mastofauna_multi_empreendimentos.py`
- `scripts/run_herpetofauna_multi_empreendimentos.py`
- `scripts/run_primatas_multi_empreendimentos.py`
- `scripts/run_pipeline.py`
- `src/opyta_analysis/runner.py`
- `src/opyta_analysis/pipelines/diagnostico/ictio_partial.py`
- `src/opyta_analysis/pipelines/diagnostico/mastofauna.py`
- `src/opyta_analysis/pipelines/diagnostico/avifauna.py`
- Sistema de migracao/validacao em `G:/Meu Drive/Opyta/Opyta_Data`

## Diagnostico atual

A base ja tem bons fundamentos:

- runner central (`opyta_analysis.runner.run`);
- padrao visual centralizado por tema;
- auditoria de saida com metadados, hashes e manifestos;
- pipelines por grupo biologico;
- validadores de importacao no projeto `Opyta_Data`;
- scripts de lote que ja rodam multiplos empreendimentos.

Mas a camada de orquestracao ainda esta especifica demais:

- campanha hardcoded nos scripts;
- caminho de saida hardcoded;
- lista de empreendimentos hardcoded;
- nomes de PCH e area controle hardcoded;
- uso de variaveis globais em modulos (`TARGET_PCH_NAME`, `TARGET_CAMPANHA`);
- cliente `fersam001` reutilizado para projetos distintos;
- script de lote sobrescreve a trilha de auditoria do grupo a cada empreendimento,
  preservando como `execution_metadata.json` apenas o ultimo alvo executado;
- cada grupo repete logica de carregamento, normalizacao, metricas e graficos;
- Avifauna ainda e stub no core, apesar de existir migrador no `Opyta_Data`.

## O que deve virar configuracao

Valores especificos de Itatiaia/Guanhaes devem sair dos scripts e ir para
arquivo de projeto/campanha:

- `project_id`;
- `client`;
- `audit_project_slug`;
- campanha alvo (`C028-2026-05-SC`);
- rotulo de pasta da campanha (`28_campanha-Abril_26`);
- raiz de entrega no Drive;
- grupos a executar;
- empreendimentos e aliases:
  - nome no banco;
  - nome de pasta;
  - slug;
  - area controle, quando existir;
- padrao de subpasta por grupo;
- mapa de pontos/amostragens, quando houver regra de interpretacao (`RP`, `TR`,
  controle, qualitativo, quantitativo);
- blocos padrao por grupo;
- regras de texto/relatorio por campanha;
- estrategia de auditoria: por grupo, por empreendimento e consolidada por lote.

Exemplo de alvo desejado:

```json
{
  "project_slug": "project_165",
  "project_id": 165,
  "client": "fersam001",
  "campaign": {
    "code": "C028-2026-05-SC",
    "folder": "28_campanha-Abril_26"
  },
  "output_root": "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhaes Energia/Resultados e analises/{campaign.folder}",
  "empreendimentos": [
    {"name": "Dores de Guanhaes", "folder": "Dores de Guanhaes"},
    {"name": "Fortuna II", "folder": "Fortuna II"},
    {"name": "Jacare", "folder": "Jacare"},
    {"name": "Senhora do Porto", "folder": "Senhora do Porto"}
  ],
  "groups": {
    "ictiofauna": {"pipeline": "ictio_partial", "block": "all"},
    "avifauna": {"pipeline": "avifauna", "block": "all"}
  }
}
```

## O que deve virar funcao reutilizavel

Prioridade alta:

- carregamento Supabase por `project_id`, `campanha`, `grupo`;
- resolucao campanha -> `id_campanha`;
- resolucao ponto -> empreendimento/campanha/tipo;
- normalizacao robusta de texto, acentos, espacos invisiveis e mojibake;
- builder de caminhos de saida;
- orquestrador de lote por grupo e empreendimento;
- coletor de resultado por lote, com resumo consolidado;
- manifestos por empreendimento, nao apenas ultimo alvo do grupo;
- validacao pre-execucao de output path, campanha, empreendimentos e dados;
- padrao unico para relatorios descritivos.

Prioridade media:

- indices: Shannon, Pielou, Simpson;
- riqueza observada;
- Jackknife 1 e Bootstrap;
- matriz presenca/ausencia;
- matriz abundancia/CPUE;
- Jaccard, Bray-Curtis;
- dendrograma com eixo de similaridade;
- Venn/overlap entre recortes;
- tabela geral de status: ameacada, endemica, rara, exotica, cinegetica,
  xerimbabo.

## Script central recomendado

Criar um runner de lote:

```powershell
python scripts/run_fauna_batch.py `
  --project-config configs/projects/itatiaia_guanhaes.json `
  --campaign C028-2026-05-SC `
  --groups ictiofauna,avifauna `
  --empreendimentos all
```

Responsabilidades:

- ler configuracao do projeto;
- resolver campanha e pasta de saida;
- montar `RunParams`;
- passar contexto de execucao sem usar variaveis globais;
- executar empreendimentos em lote;
- registrar metadados por item;
- gerar manifesto consolidado por campanha/grupo;
- falhar de forma clara quando um alvo nao tem dados;
- permitir reexecucao apenas de um grupo ou empreendimento.

## Parametrizacao necessaria

O modelo minimo de parametros deve aceitar:

- projeto: `project_id`, `project_slug`, `client`;
- campanha: codigo, pasta, periodo, data de referencia;
- grupo faunistico: nome formal, pipeline, tabela de resultados, blocos;
- empreendimento: nome no banco, nome de pasta, aliases;
- pontos amostrais: filtros opcionais, tipo de area, ambiente;
- tipo de amostragem: quantitativa, qualitativa, visual, auditiva etc.;
- saida: raiz, subpasta por grupo, subpasta por empreendimento;
- auditoria: pasta, modo de manifesto, hashes e dirty status.

## Como evitar retrabalho em novas campanhas

O fluxo desejado para campanha 29 deve ser:

1. Migrar/validar os dados novos no `Opyta_Data`.
2. Alterar somente o codigo/pasta da campanha na configuracao ou passar por CLI.
3. Rodar `run_fauna_batch.py`.
4. Receber as mesmas tabelas, graficos e relatorios por empreendimento.
5. Conferir `fauna_inventory.json` e manifesto consolidado da campanha.

Nenhum script especifico deve precisar ser copiado ou editado para trocar de
campanha.

## Padronizacao de produtos

Para cada grupo/empreendimento, o pipeline deve declarar uma lista esperada de
artefatos por bloco:

- tabelas `.xlsx`;
- figuras `.png`;
- relatorio descritivo `.txt` ou `.md`;
- metadados de execucao;
- hash e tamanho de cada arquivo.

O runner deve comparar o esperado vs. gerado e classificar:

- `OK`;
- `OK_WITH_WARNINGS`;
- `ERROR`.

## Aprendizados incorporados da ictiofauna

- Dendrograma calculado em distancia e rotulado em similaridade precisa de
  margem alem de 100%, para que pares identicos nao parecam desconectados.
- Cores dos ramos do dendrograma indicam agrupamentos hierarquicos, nao
  ambientes.
- A legenda da figura deve mencionar somente dados usados na analise. Em 6.4 de
  ictio parcial, usar `Rio Principal (RP) - dados quantitativos | cores =
  agrupamentos`.
- `TR` nao deve aparecer na legenda da similaridade se tributarios nao entram na
  matriz.
- Venn RP x TR deve registrar observacao quando nao houver TR: Jaccard zero
  indica ausencia de dado TR, nao dissimilaridade testada.
- Status `Exotica` deve distinguir `Nativo/Nativa` de `Nao Nativa/Nao Nativo` e
  termos explicitos como exotico, alocotone, introduzido ou invasor.
- Cliente e projeto nao podem ser inferidos apenas de `client`; precisa haver
  `audit_project_slug` por execucao.

## Avaliacao do uso em lote hoje

A estrutura atual permite rodar todos os empreendimentos em lote, mas ainda com
risco operacional:

- um script por grupo;
- configuracao embutida;
- nomes de campanha e caminhos fixos;
- variaveis globais para trocar alvo;
- manifestos de auditoria por grupo nao representam bem todos os alvos do lote;
- uma planilha aberta pode interromper parte do lote com `PermissionError`;
- a migracao e a analise vivem em repos diferentes sem contrato formal entre
  validacao, schema e pipeline.

## Riscos principais

- erro manual ao copiar campanha/caminho;
- divergencia entre nome no banco e nome de pasta (`Jacare` vs `Jacare` com
  acento, ou mojibake);
- filtros escondidos dentro do modulo;
- duplicacao de regras de calculo entre grupos;
- saida parcial parecer completa;
- auditoria apontar OK para o ultimo empreendimento, mas nao para todo o lote;
- rerun de um projeto gravar lastro no slug errado;
- planilhas abertas bloquearem reexecucao;
- Avifauna repetir os mesmos problemas se migrada como script isolado.

## Recomendacao para Avifauna

Antes de implementar `src/opyta_analysis/pipelines/diagnostico/avifauna.py`,
criar ou pelo menos desenhar estas bases:

1. Configuracao de projeto/campanha.
2. Runner de lote generico.
3. Funcoes compartilhadas de carregamento fauna por campanha.
4. Funcoes compartilhadas de metricas e graficos.
5. Contrato entre `Opyta_Data` e `Opyta_Data_Analysis`:
   - abas esperadas;
   - colunas obrigatorias;
   - tabelas destino;
   - validacoes bloqueantes;
   - mapeamento de esforco/resultados.

O migrador de Avifauna em `Opyta_Data/scripts/migrar_avifauna.py` ja traz uma
boa base transacional e validacoes de abas/colunas, mas deve ser refatorado no
futuro para compartilhar a logica comum com os demais grupos.

## Plano incremental

1. **Agora**: manter scripts atuais, mas registrar conhecimento e corrigir
   pontos criticos de auditoria.
2. **Antes da Avifauna**: criar configuracao de Itatiaia/Guanhaes e um
   `run_fauna_batch.py` simples.
3. **Durante Avifauna**: implementar o pipeline ja consumindo contexto
   parametrizado, sem variaveis globais.
4. **Depois da primeira campanha Avifauna**: extrair utilitarios comuns para
   `opyta_analysis.fauna`.
5. **Proxima campanha**: rodar apenas alterando `--campaign` ou a configuracao.
