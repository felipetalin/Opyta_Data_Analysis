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
- `outputs/validacoes/porto_estrela/validacao_porto_estrela_ictiofauna_20260602.*`

Os arquivos em `outputs/validacoes` sao ignorados pelo git por configuracao do repositorio.

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
