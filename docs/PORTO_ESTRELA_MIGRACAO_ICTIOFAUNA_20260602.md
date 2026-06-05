# Porto Estrela - Migracao Ictiofauna

Registro de continuidade em 2026-06-02.

## Escopo

- Projeto: Monitoramento da ictiofauna da UHE Porto Estrela.
- Codigo Opyta previsto: `BIOPOR001`.
- Cliente: Bios Consultoria e Servicos Ambientais Ltda.
- Workbook principal de migracao:
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\<pasta Migra*>\Opyta-Bios-Porto_Estrela-Ictio-2026.xlsx`
- Workbook validado gerado:
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\<pasta Migra*>\Opyta-Bios-Porto_Estrela-Ictio-2026_MIGRACAO_VALIDADA.xlsx`

Observacao: no Windows, a pasta acima aparece como `Migracao` com acento. Em scripts Python, preferir descobrir a pasta por `child.name.startswith("Migra")` para evitar problema de encoding do caminho.

## Premissas Fixadas

- Codigo tecnico de campanha: `PE###_AH####_AAAAMM`.
- Exemplo: `PE001_AH0304_200401`.
- A coluna `Observacoes_Coleta` mantem o ano hidrologico original, como `ano 03-04`.
- Rotulos curtos e rotulos de grafico/tabela ficam no arquivo de apoio `de_para_campanhas_porto_estrela_20260602.xlsx`, nao no banco principal.
- A chave de validacao de esforco e resultados e:
  `Campanha + Ponto + Metodo_de_Captura + Tipo_de_Amostragem`.
- O migrador oficial de ictiofauna ainda usa a chave:
  `Campanha + Ponto + Metodo_de_Captura`.
- Para Porto Estrela, apos limpeza, nao ha duplicidade perigosa nessa chave do migrador.

## Premissas Analiticas Aprovadas

Registro aprovado pelo usuario em 2026-06-02 para orientar as analises de
ictiofauna de Porto Estrela.

Base de especies:

- Especies com resultados migrados: 61.
- Especies no cadastro definitivo: 61.
- Migradoras derivadas: 12.
- Nao migradoras derivadas: 49.
- Nativas: 40.
- Nao nativas: 21.
- Ameacadas de extincao: 4.

Separacao de amostragem:

- Amostragem qualitativa: usar em composicao, ocorrencia, curva do coletor,
  suficiencia amostral e demais analises de presenca/ausencia.
- Amostragem quantitativa: usar como motor analitico do relatorio, com
  abundancia e biomassa padronizadas por esforco.
- `CPUEn` e a metrica central de abundancia padronizada. Ela deve orientar as
  analises estatisticas, diversidade quantitativa, similaridade e series
  temporais de abundancia.

Regra oficial de CPUE para Porto Estrela:

- O esforco deve ser interpretado por linha analitica.
- `CPUEn_linha = Numero_de_Individuos / Esforco * 100`.
- `PC_g` representa peso individual.
- `Biomassa_g_linha = Numero_de_Individuos * PC_g`.
- `CPUEb_linha = Biomassa_g_linha / Esforco * 100`.
- Depois do calculo por linha, agregar por soma conforme campanha, ano
  hidrologico, ponto, trecho, especie ou grupo ecologico.
- Para `CPUEb`, usar a planilha validada/pre-migracao como base de calculo
  quando necessario, pois o migrador oficial agrega `PC_g` por media ao
  consolidar especie+esforco.

Pipeline de CPUE aprovado em 2026-06-03:

- Secao `6.6.1`: variacao temporal e composicao das CPUEs de todas as
  especies a Montante e Jusante. Para o grafico de especies, usar tornado/top
  10 + `Outras`, sem filtro de origem.
- Para os blocos de CPUE por grupo biologico, manter o mesmo ritual de
  entrega: grafico de especies tipo tornado/top 10 + `Outras`, grafico
  espacial tipo pizza por ponto e grafico temporal com sombreado/inflexoes,
  sempre com Excel correspondente.
- Mapa espacial de todas as especies: fatias `Migradora nativa`,
  `Migradora nao nativa`, `Nao migradora nativa` e
  `Nao migradora nao nativa`.
- Mapa espacial de nativas/nao nativas: fatias `Nativa` e `Nao nativa`.
- Mapa espacial de migradoras: fatias `Migradora nativa` e
  `Migradora nao nativa`.
- Mapa espacial de ameacadas: fatias por especie ameacada, pois o grupo e
  pequeno.
- `Lophiosilurus alexandri` deve ser excluida do bloco/grafico de especies
  ameacadas para Porto Estrela, pois e exotica na bacia. Manter a especie nos
  blocos gerais e nos blocos de nao nativas/exoticas quando aplicavel.
- Tabela 8 esta aprovada.

Corte temporal aprovado:

- Rodar a primeira bateria ate dezembro de 2025.
- O corte operacional e `AAAAMM <= 202512` no codigo de campanha
  `PE###_AH####_AAAAMM`.
- Confirmacao em banco: a ultima campanha migrada e `PE090_AH2526_202512`;
  portanto as 90 campanhas ja estao dentro do corte aprovado.
- A campanha `PE055_AH1617_201703_R2` possui sufixo de rodada, mas deve ser
  interpretada temporalmente como `201703` e mantida no corte.

Trechos espaciais aprovados:

- Montante, em ordem geografica de montante para jusante: `P4`, `P5`, `P2`,
  `P1`.
- Jusante, em ordem geografica de montante para jusante: `P3`, `P6`, `P7`,
  `P8`, `P9`.

Regra reprodutiva aprovada:

- A analise reprodutiva usa as colunas `Sexo` e `EMG`.
- A classificacao macroscopica segue Bazzoli (2003):
  - `F1`/`M1`: repouso.
  - `F2`/`M2`: maturacao inicial.
  - `F3`/`M3`: maturacao avancada/maduro.
  - `F4`/`M4`: desovado/esgotado.
- A evidencia reprodutiva forte do relatorio e definida por `F3`, `M3`,
  `F4` e `M4`.
- A metrica principal e abundancia de individuos por EMG, agregada por especie,
  ponto, campanha, ano hidrologico, trecho e grupos ecologicos.
- A analise principal deve priorizar especies migradoras e/ou ameacadas, com
  aba complementar para todas as especies com `EMG` informado.

Aprendizado incorporado:

- Scripts anteriores de ictiofauna ja usam CPUE como `valor / esforco * 100`.
- Diversidade e similaridade quantitativas devem usar matriz baseada em
  `CPUEn`.
- Linhas auxiliares de captura zero podem completar graficos por ponto, mas
  nao devem entrar em composicao, taxonomia, curvas ou analises comunitarias
  como registros reais de especie.
- Para Porto Estrela, se houver conflito com scripts que usam esforco total por
  ponto, prevalece a regra por linha definida acima.

## Arquivos Gerados

Na pasta de migracao do cliente:

- `Pontos_e_Campanhas_MIGRACAO.xlsx`
- `de_para_campanhas_porto_estrela_20260602.xlsx`
- `Metadados_Esforco_MIGRACAO.xlsx`
- `validacao_metadados_esforco_porto_estrela_20260602.md`
- `Opyta-Bios-Porto_Estrela-Ictio-2026_MIGRACAO_VALIDADA.xlsx`
- `validacao_resultados_ictiofauna_porto_estrela_20260602.md`
- `lista_especies_porto_estrela_ictiofauna_20260602.xlsx`

No repositorio:

- `scripts/validar_migracao_ictiofauna.py`
- `scripts/gerar_base_analitica_porto_estrela_ictio.py`
- `scripts/gerar_modelos_graficos_porto_estrela_ictio.py`
- `scripts/gerar_resultados_porto_estrela_ictio.py`
- `outputs/validacoes/porto_estrela/validacao_porto_estrela_ictiofauna_20260602.*`

Os arquivos em `outputs/validacoes` sao ignorados pelo git por configuracao do repositorio.

Na pasta temporaria de resultados do cliente:

- `caracterizacao_especies_porto_estrela_20260602.xlsx`
- `de_para_pontos_trechos_porto_estrela_20260602.xlsx`
- `base_analitica_ictiofauna_porto_estrela_20260602.xlsx`
- `base_analitica_ictiofauna_porto_estrela_20260602.md`
- `modelos_graficos_porto_estrela_20260602\`
- `resultados_ictiofauna_porto_estrela_20260602\`

Na pasta oficial de resultados gerada em 2026-06-02:

- Saida unica, sem subpastas numeradas, para facilitar revisao visual.
- Cada produto possui prefixo proprio no nome do arquivo, como `tabela_05`,
  `figura_13`, `secao_663`.
- O script oficial continua modular por bloco e permite rerodar apenas um
  subconjunto com `--only`, por exemplo:
  `python scripts\gerar_resultados_porto_estrela_ictio.py --only 14`

Documentos de apoio:

- `docs/PORTO_ESTRELA_LAYOUT_GRAFICOS_REFERENCIA_DUCAL_20260602.md`
- `docs/PORTO_ESTRELA_MATRIZ_PRODUTOS_ICTIOFAUNA_20260602.md`

## Estado das Abas

### Pontos_e_Campanhas

- Linhas: 608.
- Campanhas: 90.
- Pontos unicos: 9.
- Campanhas convertidas para o padrao `PE###_AH####_AAAAMM`.
- `Observacoes_Coleta` mantida com o ano hidrologico.

### Metadados_Esforco

- Entrada original: 1110 linhas.
- Saida padronizada: 1108 linhas.
- Foram removidas 2 duplicidades exatas:
  - `PE064_AH1819_201906 | P4 | Arrasto | Qualitativa`
  - `PE070_AH2021_202012 | P4 | Arrasto | Qualitativa`
- `N.A.` em `Esforco` foi convertido para celula vazia, para nao bloquear o validador numerico.
- Sem duplicidades na chave do migrador.
- Sem duplicidades na chave do validador.

### Resultados_Ictiofauna

- Linhas: 25069.
- Campanhas: 90.
- Pontos: 9.
- Metodos: 4 (`Rede`, `Arrasto`, `Tarrafa`, `Anzol`).
- Tipos de amostragem: 2 (`Quantitativa`, `Qualitativa`).
- Nomes cientificos: 61.
- A coluna `Observacao` foi renomeada para `Observacoes_Coleta`.
- Campanhas antigas, como `abr-04`, foram convertidas usando `Campanha original + Observacoes_Coleta`.
- Espacos invisiveis em nomes cientificos foram normalizados.

## Validacao Atual

Validacao estrutural cruzada:

- `Campanha + Ponto` contra `Pontos_e_Campanhas`: 0 problemas.
- `Campanha + Ponto + Metodo + Tipo` contra `Metadados_Esforco`: 0 problemas.
- Chave do migrador `Campanha + Ponto + Metodo`: 0 problemas.

Validacao oficial direta de `Opyta_Data`:

- Bloqueios reais: 1.
- Bloqueio: `UNKNOWN_SPECIES`, com 38 especies ainda nao cadastradas no banco.
- Aviso: `PROJECT_NOT_FOUND`, esperado nesta fase porque `BIOPOR001` ainda sera criado na migracao.

O validador complementar do wrapper tambem sinalizou alguns itens conservadores:

- `CAMPAIGN_DATE_MISMATCH`: artefato do codigo de campanha novo com ano hidrologico embutido. A data confere com o trecho `AAAAMM` do codigo, mas o wrapper ainda espera padrao antigo.
- `MISSING_REQUIRED_FIELDS`: inclui esforco vazio para amostragem qualitativa e biometria ausente em alguns registros. Nao foi bloqueio no validador oficial direto.
- `EXACT_RESULT_DUPLICATES`: ha registros biometricos iguais. Para ictiofauna isso pode representar individuos distintos; confirmar antes de qualquer deduplicacao.

## Especies Pendentes no Banco

Total: 38.

- `Astyanax bimaculatus`
- `Astyanax sp.`
- `Brycon cf. falcatus`
- `Brycon dulcis`
- `Bryconamericus stramineus`
- `Characidium cf. timbuiense`
- `Clarias gariepinus`
- `Corydoras aeneus`
- `Crenicichla lacustris`
- `Cyphocharax gilbert`
- `Cyprinus carpio`
- `Deuterodon pedri`
- `Glanidium cf. melanopterum`
- `Henochilus wheatlandii`
- `Hyphessobrycon eques`
- `Leporinus sp.`
- `Lophiosilurus alexandri`
- `Loricariichthys castaneus`
- `Megaleporinus conirostris`
- `Megaleporinus macrocephalus`
- `Metynnis maculatus`
- `Moenkhausia vittata`
- `P. reticulatum x L. marmoratus`
- `Pachyurus adspersus`
- `Piaractus mesopotamicus`
- `Pimelodella sp.`
- `Pimelodus maculatus`
- `Pogonopoma wertheimeri`
- `Prochilodus costatus`
- `Prochilodus vimboides`
- `Psalidodon fasciatus`
- `Pseudauchenipterus affinis`
- `Pseudoplatystoma sp.`
- `Pygocentrus nattereri`
- `Salminus brasiliensis`
- `Synbranchus marmoratus`
- `Trichomycterus cf. alternatus`
- `Trichomycterus sp.`

## Plano Para Retomada

1. Criar/usar um `de_para_taxonomico_porto_estrela.xlsx`.
2. Para cada uma das 38 especies pendentes, decidir:
   - cadastrar como nova;
   - mapear para nome aceito atualizado;
   - manter como unidade taxonomica operacional (`sp.`, `cf.`, `aff.`, hibrido);
   - atualizar cadastro do banco com cautela, quando o banco estiver desatualizado.
3. Nao atualizar o banco as cegas: a tabela `especies` e compartilhada por outros projetos.
4. Gerar planilha `Cadastro_Especies` ou arquivo separado de cadastro com as especies resolvidas.
5. Rodar novamente o validador oficial.
6. So seguir para migracao quando o bloqueio `UNKNOWN_SPECIES` zerar ou quando houver uma decisao explicita de cadastro integrado.

## Comandos Uteis

Validacao oficial direta:

```powershell
$parent = "G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha"
$mig = (Get-ChildItem -LiteralPath $parent -Directory | Where-Object { $_.Name -like "Migra*" } | Select-Object -First 1).FullName
$wb = Join-Path $mig "Opyta-Bios-Porto_Estrela-Ictio-2026_MIGRACAO_VALIDADA.xlsx"
python "G:\Meu Drive\Opyta\Opyta_Data\scripts\validar_importacao.py" $wb Ictiofauna
```

Validacao complementar no repositorio:

```powershell
$parent = "G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha"
$mig = (Get-ChildItem -LiteralPath $parent -Directory | Where-Object { $_.Name -like "Migra*" } | Select-Object -First 1).FullName
$wb = Join-Path $mig "Opyta-Bios-Porto_Estrela-Ictio-2026_MIGRACAO_VALIDADA.xlsx"
python scripts\validar_migracao_ictiofauna.py --import-file $wb --project-slug porto_estrela --expected-campaigns 90 --expected-result-lines 25069 --expected-species 61 --stamp 20260602
```

## Proximo Ponto de Conversa

Comecar pela decisao taxonomica. A pergunta central e:

- quais das 38 especies devem ser nomes aceitos novos;
- quais sao sinonimos/nomes antigos ja representados no banco;
- quais devem permanecer como unidades operacionais de relatorio.

Depois disso, aplicar o de/para nos resultados ou cadastrar as especies pendentes e rodar nova validacao.

## Correcoes Taxonomicas Aprovadas

- 2026-06-02: corrigida a familia `Acestrorhamphinae` para `Acestrorhamphidae` no Supabase (`especies`, 9 registros), na caracterizacao local e no cadastro definitivo de especies. Produtos afetados regenerados: Tabela 5 e Figura 11.

## Correcoes De Pontos

- 2026-06-03: corrigida a coordenada do ponto `P1` no Supabase
  (`pontos_coleta`, `BIOPOR001`, `id_projeto=186`), em 90 linhas:
  latitude `-19.108602` e longitude `-42.662967`.
- Os mapas espaciais exploratorios gerados antes dessa correcao nao foram
  regenerados por decisao do usuario; eles permanecem apenas como prova visual
  de conceito. O proximo rerun deve usar a coordenada corrigida.

## Checkpoint Para Retomada

Registro de fechamento em 2026-06-02:

- Resultados previstos gerados na pasta unica
  `resultados_ictiofauna_porto_estrela_20260602`, sem subpastas numeradas.
- Script oficial modular por bloco:
  `scripts/gerar_resultados_porto_estrela_ictio.py`.
- O parametro `--only` aceita codigos com ou sem zero a esquerda, por exemplo
  `--only 5`, `--only 05`, `--only 10` ou listas como `--only 13,14`.
- Figura 10 ajustada para deixar explicito que a curva observada e a media das
  aleatorizacoes, o Jackknife 1 e a estimativa media e as faixas sombreadas sao
  `+/- 1 DP`.
- A revisao de amanha deve seguir item a item, ajustando e rerodando somente o
  bloco afetado.

## Analises Exploratorias Fora do Escopo

- 2026-06-03: criada bancada separada para testar diversidade beta temporal
  Montante x Jusante, LCBD, PCoA exploratoria e pontos de inflexao em CPUE.
- Registro tecnico: `docs/PORTO_ESTRELA_ANALISES_EXPLORATORIAS_BETA_INFLEXAO_20260603.md`.
- Pasta de teste:
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\resultados_ictiofauna_porto_estrela_20260602\testes_analises_exploratorias_beta_inflexao_20260603`.
- Estes produtos permanecem fora do escopo oficial ate avaliacao e aprovacao.
- 2026-06-03: geradas duas alternativas em paleta azul, sem titulo interno,
  para os componentes de diversidade beta por presenca/ausencia entre anos
  hidrologicos consecutivos: `exploratoria_10_beta_pa_componentes_trechos_comparativo_azul.png`
  (Montante e Jusante no mesmo painel) e
  `exploratoria_11_beta_pa_componentes_por_area_azul.png` (paineis separados
  por area). Metricas: Turnover (`beta-sim`), `beta-Sorensen` (`beta-sor`) e
  Nestedness (`beta-nes`).
- 2026-06-03: criada bancada separada para testar visualizacoes espaciais
  exploratorias com mapas de bolhas, pizzas espaciais, colares de bolhas,
  mapas de calor ponto x ano hidrologico e perfil longitudinal.
- Pasta de teste:
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\resultados_ictiofauna_porto_estrela_20260602\testes_analises_exploratorias_espaciais_bolhas_colar_20260603`.

## Padroes Graficos Aprovados

- 2026-06-03: Figura 16 ajustada para grafico espelhado
  (`butterfly`/`tornado`) comparando `CPUEn (%)` e `CPUEb (%)` entre
  Montante e Jusante no recorte atual (`AH2324`, `AH2425`, `AH2526`).
  Regra de exibicao: selecionar ate 10 especies nativas principais por
  metrica, agregando as demais em `Outras especies nativas`, sempre como a
  ultima linha do painel, independentemente do percentual.
- 2026-06-03: aprovado como referencia espacial o mapa de pizzas por ponto,
  sem imagem satelite, sem titulo interno, com legenda horizontal superior,
  linhas de trecho em azul/laranja, rotulos afastados com linhas guia e P1 com
  coordenada corrigida. Arquivo de referencia:
  `espacial_03_mapa_pizzas_grupos_cpuen_pontos_teste_relatorio.png`.
- A versao com imagem satelite foi testada e nao foi aprovada para este fim,
  pois reduz a legibilidade analitica.
- 2026-06-03: aprovado como referencia temporal com inflexao o painel sem
  linha de tendencia, em paleta azul, sem titulo interno, com serie temporal
  limpa, linhas verticais discretas nos pontos de inflexao fortes e sombreado
  das ultimas AHs. Arquivo de referencia:
  `exploratoria_06_inflexao_cpueb_migracao_origem_v3_sem_tendencia_azul.png`.
- Para graficos temporais com inflexao, manter o sombreado das ultimas AHs
  (`AH2324`, `AH2425`, `AH2526`) e usar paleta azul. A versao com regressao
  fracionada antes/depois foi testada, mas ficou visualmente carregada para o
  painel principal. Recomendacao atual: usar serie temporal limpa com linhas
  verticais discretas nos pontos de inflexao fortes; manter as regressões como
  apoio tecnico em tabela/nota metodologica.

## Producao De Resultados

- 2026-06-03: gerada nova pasta de producao dos resultados:
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\resultados_ictiofauna_porto_estrela_producao_20260603`.
- A pasta antiga `resultados_ictiofauna_porto_estrela_20260602` foi mantida
  como historico/referencia.
- O script oficial `scripts/gerar_resultados_porto_estrela_ictio.py` passou a
  gerar, por padrao, a pasta de producao `20260603`, usando as bases aprovadas
  `base_analitica_ictiofauna_porto_estrela_20260602.xlsx` e
  `caracterizacao_especies_porto_estrela_20260602.xlsx`.
- Producao oficial do pipeline: 53 arquivos, sendo 51 produtos no manifesto
  mais `manifesto_resultados_ictiofauna_porto_estrela.xlsx` e
  `manifesto_resultados_ictiofauna_porto_estrela.md`.
- A pasta tambem pode conter arquivos manuais de apoio fora do manifesto, como
  `Layout tabelas.xlsx`; esses nao sao saidas oficiais do pipeline.
- Manifestos finais:
  `manifesto_resultados_ictiofauna_porto_estrela.xlsx` e
  `manifesto_resultados_ictiofauna_porto_estrela.md`.
- Blocos novos incorporados em producao:
  - `661`: 6.6.1, todas as especies;
  - `662`: 6.6.2, nativas/nao nativas;
  - `663`: 6.6.3, migradoras nativas/nao nativas;
  - `664`: 6.6.4, ameacadas, excluindo `Lophiosilurus alexandri`;
  - `31`: diversidade beta temporal por area;
  - `32_33`: reproducao com abundancia relativa e mapa espacial de EMG.

## Pontos De Inflexao Aprovados

- 2026-06-03: aprovado como padrao estatistico para os graficos temporais de
  CPUE o teste de `ponto de inflexao` por regressao segmentada.
- Metodo aprovado: regressao linear simples como modelo nulo; regressao
  segmentada com termo hinge e ponto de inflexao escolhido por menor SSE como
  modelo alternativo; minimo de 5 anos hidrologicos por segmento; teste global
  por permutacao dos residuos sob o modelo linear nulo; correcao
  Benjamini-Hochberg entre as series testadas.
- Regra grafica aprovada: marcar linha vertical somente quando `p_BH <= 0,05`.
  O sombreado dos anos hidrologicos recentes deve cobrir explicitamente
  `AH2324`, `AH2425` e `AH2526`.
- O teste foi incorporado aos graficos temporais de CPUE dos blocos `661`,
  `662`, `663` e `664`, tanto para `CPUEn` quanto para `CPUEb`.
- Os resultados estatisticos ficam dentro do Excel de cada bloco, nas abas
  `Ponto_Inflexao_CPUEn` e `Ponto_Inflexao_CPUEb`.
- Arquivos avulsos de teste (`teste_estatistico_*`) foram removidos da pasta
  de producao para manter apenas os produtos oficiais incorporados aos blocos.

## Padroes De Rotulos De Especies

- 2026-06-03: padronizado o destaque dos nomes de especies em graficos tipo
  tornado/lollipop com o nome cientifico limpo, sem sufixos como `MN` ou
  `MNN`. A classificacao biologica deve aparecer por cor no rotulo do eixo
  vertical e por legenda superior do grafico.
- Paleta aprovada para rotulos de especies: `MN` = migradora nativa em verde
  escuro (`#00441B`); `MNN` = migradora nao nativa em vermelho escuro
  (`#67000D`); `NMN` = nao migradora nativa em verde (`#41AB5D`);
  `NMNN` = nao migradora nao nativa em vermelho alaranjado (`#EF6548`). Os codigos ficam
  apenas como classe interna/Excel (`Classe_Biologica`), nao no nome exibido.
- A legenda superior dos graficos com nomes de especies deve representar as
  categorias biologicas presentes no grafico. A indicacao Montante/Jusante
  permanece no corpo do tornado, pelas laterais e cores das barras.
- Os rotulos de especies nos eixos devem ficar em italico e negrito quando
  representarem nome cientifico; `Outras especies` permanece sem italico.
- Padrao aplicado nos graficos com nomes de especies dos blocos `15`, `16`,
  `661`, `662`, `663` e `664`.
- No bloco `664` (ameacadas), a linha `Outras especies` nao deve ser gerada:
  o tornado deve exibir apenas as 3 especies validas para Porto Estrela,
  excluindo `Lophiosilurus alexandri` conforme decisao tecnica do projeto.

## Ajustes De Layout - 2026-06-04

- Figura 12 deve usar o mesmo sombreado dos anos hidrologicos recentes
  (`AH2324`, `AH2425`, `AH2526`) e incluir esse item na legenda superior.
- Figura 30 deve seguir a mesma regra: sombreado dos anos hidrologicos
  recentes e legenda superior com `Montante`, `Jusante` e
  `Anos hidrologicos recentes`.
- Graficos temporais dos blocos `661`, `662`, `663` e `664`: usar legenda
  superior sem sobrepor os titulos dos paineis, eixo Y compartilhado por
  metrica (`CPUEn` ou `CPUEb`) e sombreado dos anos recentes.
- No bloco `664`, titulos dos paineis temporais e legenda do mapa de pizza
  devem usar italico, pois representam nomes cientificos.
- Figuras 32 e 33: paineis Montante/Jusante devem ficar empilhados
  verticalmente (`2 x 1`), nao lado a lado, para ganhar largura util e
  melhorar encaixe no relatorio.
- Figura 34: mapa de pizzas de EMG de femeas migradoras deve ser separado em
  dois paineis verticais no mesmo arquivo, `Migradoras nativas` e
  `Migradoras nao nativas`. A legenda de EMG deve ser descritiva:
  `F1 - Repouso`, `F2 - Maturacao inicial`, `F3 - Maduro`,
  `F4 - Desovado`.

## Padrao Gold Reutilizavel Dos Blocos

- O script oficial dos resultados e `scripts/gerar_resultados_porto_estrela_ictio.py`.
  Ele deve ser a fonte dos graficos e planilhas finais; ajustes manuais em
  imagem devem ser evitados.
- Cada produto grafico deve ter uma planilha `.xlsx` correspondente com os
  dados usados na figura. Para blocos compostos (`661` a `664`), o Excel deve
  conter abas de especies, tornado, temporal, ponto de inflexao e espacial.
- A pasta de producao deve permanecer em nivel unico, sem subpastas numeradas,
  para facilitar revisao visual e ajustes pontuais. A modularidade fica no
  codigo e nos nomes dos arquivos.
- O comando `--only` deve ser usado para rerodar blocos especificos. Quando os
  51 produtos oficiais ja existem na pasta, o script recompõe o manifesto
  oficial completo mesmo apos execucao parcial.
- Sombreamento de anos recentes: aplicar de forma consistente a `AH2324`,
  `AH2425` e `AH2526` nas series temporais aprovadas e incluir legenda
  explicita do sombreado.
- Pontos de inflexao: usar regressao segmentada com teste por permutacao e
  correcao Benjamini-Hochberg; marcar no grafico somente quando
  `p_BH <= 0,05`.
- Graficos de especies por trecho: priorizar tornado/butterfly para comparar
  Montante x Jusante; nomes cientificos limpos, em italico/negrito, e classe
  biologica indicada por cor e legenda superior.
- Mapas de pizza: usar fundo limpo, sem satelite; linhas de trecho em
  azul/laranja; rotulos de pontos afastados com linhas guia; legenda superior
  horizontal; P1 com coordenada corrigida.
- Mapas de pizza dos blocos de CPUE (`661`, `662`, `663` e `664`): o arquivo
  espacial deve conter dois paineis verticais no mesmo PNG, com `CPUEn` acima e
  `CPUEb` abaixo, mantendo a mesma legenda de grupos biologicos e de trechos.
  As escalas de tamanho das pizzas sao independentes por metrica. O canvas
  aprovado e A4 em paisagem (`16,54 x 11,69` pol., 300 dpi) para encaixe no
  relatorio.
- No mapa espacial do bloco `662` (nativas/nao nativas), a paleta aprovada e:
  `Nativa` em verde (`#2E7D32`) e `Nao nativa` em vermelho (`#C0392B`), para
  nao confundir as categorias biologicas com as linhas de trecho
  Montante/Jusante.
- Reproducao: usar barras empilhadas por EMG e mapas de pizza por EMG; quando
  houver comparacao Montante/Jusante ou nativa/nao nativa, preferir paineis
  verticais para maximizar largura util.
- Arquivos manuais de apoio, como `Layout tabelas.xlsx`, podem permanecer na
  pasta, mas nao entram no manifesto oficial do pipeline.

## Fechamento Final - 2026-06-04

- Todos os modelos finais de graficos e tabelas foram aprovados como padrao
  gold para Porto Estrela e como referencia reutilizavel para outros projetos
  de ictiofauna.
- Pasta oficial de producao:
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\resultados_ictiofauna_porto_estrela_producao_20260603`.
- Pipeline oficial de resultados:
  `scripts/gerar_resultados_porto_estrela_ictio.py`.
- Relatorio tecnico HTML de apoio a redacao:
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\resultados_ictiofauna_porto_estrela_producao_20260603\relatorio_tecnico_ictiofauna_porto_estrela_20260604.html`.
- Versao autonoma para celular, com figuras embutidas no proprio HTML:
  `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\resultados_ictiofauna_porto_estrela_producao_20260603\relatorio_tecnico_ictiofauna_porto_estrela_20260604_autonomo_celular.html`.
- Script do relatorio HTML:
  `scripts/gerar_relatorio_html_porto_estrela_ictio.py`.
- Validacao do relatorio HTML em 2026-06-04: `py_compile` aprovado; 33 figuras,
  13 tabelas e 105 referencias internas entre imagens e planilhas, sem links
  quebrados.
- Validacao da versao autonoma para celular: 33 imagens embutidas em base64,
  aproximadamente 22,5 MB; permanece com links relativos para os Excels de
  apoio quando aberta no computador, mas nao depende dos PNG externos para
  exibir as figuras.
- Os modelos aprovados devem ser ajustados sempre pelo script/bloco de origem,
  preservando Excel de apoio, manifesto e nomes oficiais dos arquivos.
- Este registro encerra a etapa de organizacao dos resultados analiticos de
  Porto Estrela. A proxima etapa e revisao de texto/interpretacao fina no
  relatorio consolidado.
