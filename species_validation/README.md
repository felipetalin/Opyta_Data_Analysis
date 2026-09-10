# Validador De Cadastro De Especies

Este diretorio guarda o lastro do validador taxonomico usado antes da entrada
de especies no banco.

## Objetivo

Conferir a planilha de cadastro de especies antes da importacao para o banco,
mantendo rastreabilidade entre:

- nome recebido na planilha;
- nome encontrado na base taxonomica;
- nome aceito atualizado;
- familia e hierarquia retornadas;
- fonte consultada;
- data da validacao;
- decisao automatica ou pendencia de revisao.

## Fontes

O perfil geral usa o GBIF Backbone Taxonomy via Species Match API. O perfil
`zooplankton` consulta WoRMS, Catalogo Taxonomico da Fauna do Brasil (CTFB) e
GBIF. Uma atualizacao automatica so ocorre quando as tres bases aceitam o mesmo
nome e nao apresentam conflito nos campos taxonomicos comparaveis.

Prioridade sugerida por grupo:

| Grupo | Fonte primaria | Fontes auxiliares |
|---|---|---|
| Flora Brasil | Flora e Funga do Brasil | POWO, WFO, GBIF, IPNI |
| Fungos | Flora e Funga do Brasil, MycoBank, Index Fungorum | GBIF, COL |
| Algas | Flora e Funga do Brasil, AlgaeBase | GBIF, COL |
| Fauna geral | Catalogue of Life, GBIF | bases especializadas |
| Marinhos | WoRMS | GBIF, COL |
| Zooplancton | WoRMS, CTFB, GBIF | consenso obrigatorio das tres bases |

## Uso

Exemplo com uma planilha Excel:

```powershell
python scripts\validation\species\validar_cadastro_especies.py `
  --input caminho\cadastro_especies.xlsx `
  --sheet Sheet1 `
  --profile zooplankton `
  --output species_validation\outputs\cadastro_especies_validated.xlsx
```

Exemplo com CSV:

```powershell
python scripts\validation\species\validar_cadastro_especies.py `
  --input caminho\cadastro_especies.csv `
  --output species_validation\outputs\cadastro_especies_validated.csv
```

O script tenta detectar automaticamente a coluna de nome cientifico. Tambem e
possivel informar explicitamente:

```powershell
python scripts\validation\species\validar_cadastro_especies.py `
  --input caminho\cadastro.xlsx `
  --name-column nome_cientifico `
  --family-column familia `
  --kingdom-column reino
```

## Saidas

A planilha validada recebe o bloco oficial de cadastro. No perfil
`zooplankton`, os valores do profissional sao preservados quando existe
conflito, ausencia em uma das bases ou falta de consenso. Campos vazios sem
informacao nas bases permanecem `N.A.`. Nao ha inferencia automatica.

Bloco de cadastro:

- `Nome_Cientifico`;
- `Nome_Popular`;
- `Grupo_Biologico`;
- `Reino`;
- `Filo`;
- `Classe`;
- `Ordem`;
- `Familia`;
- `Genero`;
- `bmwp_score`;
- `Autor_e_Ano`;
- `Status_Ameaca_Estadual`;
- `Status_Ameaca_Nacional`;
- `Status_Ameaca_Global`;
- `Origem`;
- `Habito_Alimentar`;
- `Estrategia_Reprodutiva`;
- `Valor_Economico`;
- `Observacoes`;
- `Cinegetica`;
- `Xerimbabo`.

No MVP com GBIF, os campos normalmente disponiveis sao nome cientifico aceito,
nome popular quando houver vernacular em portugues, reino, filo, classe, ordem,
familia, genero e autoria. Campos ecologicos, economicos, ameaca, BMWP,
cinegetica e xerimbabo ficam como `N.A.` ate haver fonte especifica conectada.

Se a planilha de entrada ja tiver alguma coluna do bloco oficial, o valor
original e preservado com prefixo `input_`. No perfil `zooplankton`, a coluna
oficial representa o valor final: consenso das tres bases quando aprovado ou
valor profissional quando houver pendencia.

Tambem sao adicionadas colunas de lastro com prefixo `opyta_`:

- `opyta_validation_status`;
- `opyta_taxonomic_status`;
- `opyta_matched_name`;
- `opyta_accepted_name`;
- `opyta_usage_key`;
- `opyta_accepted_usage_key`;
- `opyta_confidence`;
- `opyta_match_type`;
- `opyta_rank`;
- `opyta_kingdom`;
- `opyta_phylum`;
- `opyta_class`;
- `opyta_order`;
- `opyta_family`;
- `opyta_genus`;
- `opyta_family_check`;
- `opyta_source`;
- `opyta_validated_at`;
- `opyta_validation_notes`.

Um manifesto JSON e gerado em `species_validation/traces/` com os parametros da
execucao, contagens por status e fonte utilizada.

## Decisao Antes Do Banco

Registros com `opyta_validation_status = approved` podem seguir para cadastro
automatico, se o projeto aceitar essa regra.

No perfil `zooplankton`, somente `approved_consensus` representa consenso das
tres bases. `review_partial`, `review_conflict` e `not_found` preservam o valor
profissional e exigem decisao antes do banco.

Registros com `review` devem ser revisados antes do banco. Entram nessa classe
nomes sinonimizados, conflitos de familia, baixa confianca, nomes nao
encontrados e erros de consulta.
