# Diretriz De Planilha Para Táxons Não Cadastrados

## Regra Obrigatória

Em toda auditoria de espécies, quando houver táxons da fonte que não estejam
cadastrados no Supabase, gerar automaticamente uma planilha de pendências
taxonômicas na pasta raiz de migração do projeto. Não solicitar essa decisão ao
usuário nem interromper a operação aguardando instrução adicional.

## Momento No Fluxo

A regra é executada logo após a auditoria do cadastro, dentro da etapa
**Cadastro e auditoria de espécies** e antes do Gate B.

## Arquivo

- nome: `Cadastro_Especies_<CODIGO>_<GRUPO>.xlsx`;
- local: pasta raiz de migração do projeto;
- conteúdo: apenas um registro por táxon não cadastrado, preservando
  exatamente o nome científico da fonte;
- incluir também uma aba ou campo de pendências para táxons já existentes com
  atributos obrigatórios incompletos.

## Campos Mínimos

`Nome_Cientifico`, `Grupo_Biologico`, `Situacao_Cadastro`, `Reino`, `Filo`,
`Classe`, `Ordem`, `Familia`, `Genero`, `Autor_e_Ano`, `Fonte_Taxonomica`,
`Observacao` e `Status_Preenchimento`.

`Situacao_Cadastro` deve distinguir `novo_no_supabase` de
`completar_cadastro_existente`. Os campos taxonômicos ficam em branco para
preenchimento ou correção pelo usuário; não inferir classificação sem fonte
auditável.

## Gate B

Após a devolução da planilha preenchida, revalidar os táxons, aplicar o
cadastro/atualização no Supabase e apresentar o Gate B. A geração da planilha
é automática; a aprovação taxonômica continua explícita.

## Aplicação Atual

Para WSPKIN001 — Fitoplâncton, a planilha deve conter os 10 táxons novos e as
duas pendências de complemento (`Euastrum sp.` e `Phacus orbicularis`).
