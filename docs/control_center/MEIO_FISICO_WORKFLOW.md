# Fluxo De Migracao - Meio Fisico

Este fluxo adapta o protocolo canonico da Central de Controle para dados
fisicoquimicos. Ele preserva os mesmos gates usados na biota, mas substitui a
etapa taxonomica por uma auditoria de cadastro de parametros e VMP.

## Ordem Obrigatoria

```text
abertura
  -> validacao dos dados
  -> Gate A - dados
  -> auditoria de parametros/VMP
  -> Gate B - parametros ou nao aplicavel justificado
  -> migracao
  -> consolidacao
  -> configuracao das analises
  -> Gate C - template/paleta/saida/produtos
  -> geracao
  -> revisao
  -> fechamento
```

## Entradas Esperadas

### Planilha De Resultados

Arquivo padrao: `Resultados_Meio_Fisico.xlsx`.

Abas esperadas:

- `Capa_Projeto`;
- `Pontos_e_Campanhas`;
- `Resultados_Meio_Fisico`.

Colunas minimas em `Resultados_Meio_Fisico`:

- `Ponto`;
- `Campanha`;
- `Matriz`;
- `Parametro`;
- `Resultado`;
- `Unidade_Medida`;
- `Laboratorio`.

Colunas minimas em `Pontos_e_Campanhas`:

- `Ponto`;
- `Campanha`;
- `Data`;
- `Latitude`;
- `Longitude`.

Quando houver KMZ/KML, shapefile, planta, planilha de campo ou outra fonte
espacial oficial, ela deve ser registrada e comparada contra
`Pontos_e_Campanhas` antes do Gate A. Se a referencia externa nao existir, a
ausencia deve aparecer como ressalva explicitamente aprovada no Gate A.

### Cadastro De Parametros/VMP

O meio fisico nao usa cadastro de especies. A etapa equivalente e a auditoria
de parametros e limites legais.

Regra preferencial: usar o cadastro mestre de parametros/VMP ja existente e
gerar apenas um delta controlado para parametros novos, sinonimos, unidades ou
limites divergentes. Esse delta deve ser revisado antes de alterar o cadastro,
seguindo a mesma logica usada na biota para especies novas.

Fontes aceitas:

- `cadastro_parametros_opyta.xlsx`;
- colunas `vmp_*` ja presentes na base de migracao;
- lookup controlado em cadastro mestre, desde que a fonte e a regra de uso
  fiquem registradas na operacao.

Sem VMP, a migracao bruta pode ser planejada apenas se o usuario aceitar essa
restricao no Gate A. A geracao de conformidade, percentual de violacao e
sintese deve ficar bloqueada ate a resolucao do cadastro de parametros.

## Auditoria De Delta

A auditoria de parametros deve classificar cada combinacao `Matriz +
Parametro` em:

- `matched`: ja existe no cadastro mestre e pode ser reutilizada;
- `synonym_review`: parece sinonimo de parametro existente e precisa decisao;
- `unit_review`: parametro existe, mas unidade ou base de expressao difere;
- `vmp_review`: parametro existe, mas o VMP do laudo diverge do cadastro;
- `new_parameter`: nao encontrado no cadastro mestre;
- `not_applicable`: parametro sem VMP aplicavel, registrado apenas para serie
  temporal ou contexto de campo.

Somente itens `new_parameter`, `synonym_review`, `unit_review` e `vmp_review`
devem gerar acao de cadastro. Itens `matched` entram na migracao usando os
atributos existentes.

## Validacao Minima

A validacao pre-migracao deve registrar:

- codigo interno Opyta e nome do projeto;
- hash da planilha;
- numero de linhas por aba;
- numero de registros de resultados;
- matrizes, campanhas, pontos e parametros;
- auditoria de coordenadas: presenca, faixa valida, CRS/sistema, sinais de
  latitude/longitude invertidas, variacao por ponto/campanha e comparacao com
  fonte espacial oficial quando disponivel;
- erros de parse em `Resultado`;
- sinais de limite (`<`, `<=`, `>`, `>=`);
- nulos criticos;
- duplicidade no grao `Ponto + Campanha + Matriz + Parametro + Laboratorio`;
- pares `Ponto + Campanha` ausentes na base de pontos;
- ausencia ou origem dos VMPs.

## Gates

| Gate | Interpretacao em meio fisico | Avanco permitido |
| --- | --- | --- |
| A - dados | Resultados, pontos, coordenadas, campanhas, matrizes e parse aceitos. | Auditoria de parametros/VMP. |
| B - parametros | Cadastro de parametros e VMP aceito, ou nao aplicavel justificado. | Migracao. |
| C - analises | Template, paleta, pasta de saida e produtos confirmados. | Geracao. |

## Migracao

Antes de inserir dados:

- confirmar se o projeto existe no Supabase;
- definir `codigo_interno_opyta`;
- consultar totais existentes para evitar duplicidade;
- definir estrategia de reversao ou backup;
- executar carga controlada;
- comparar totais fonte x banco por matriz, campanha e ponto.

## Consolidacao E Analise

Depois da carga:

- auditar `fisico_analise_consolidada` por `codigo_interno_opyta`;
- conferir valores com sinal de limite;
- conferir VMPs por matriz e parametro;
- gerar produtos apenas depois do Gate C;
- exigir manifesto ou evidencia equivalente no fechamento.
