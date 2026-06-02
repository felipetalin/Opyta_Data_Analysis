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
