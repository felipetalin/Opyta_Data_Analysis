# ITAGUA001 - Ictiofauna C029 - Auditoria do cadastro existente

Consulta somente leitura em 2026-09-08. Os 14 nomes da fonte correspondem exatamente a registros existentes; nenhum cadastro novo necessario. Esta auditoria verifica completude do banco, nao atualidade taxonomica externa. Nenhum atributo foi alterado.

| Especie | ID | Ameaca nacional | Ameaca global | Origem | Endemismo | Status estadual existente |
| --- | --- | --- | --- | --- | --- | --- |
| Astyanax lacustris | 3754 | Não listada | LC | Nativo | VAZIO | Não listada (MG) |
| Cichla kelberi | 4754 | VAZIO | VAZIO | Não Nativo | VAZIO | VAZIO |
| Delturus carinotus | 4757 | VAZIO | VAZIO | Nativo | VAZIO | VAZIO |
| Deuterodon taeniatus | 4758 | VAZIO | VAZIO | Nativo | VAZIO | VAZIO |
| Geophagus brasiliensis | 4 | Não listada | LC | Nativo | VAZIO | Não listada (MG) |
| Hoplias intermedius | 629 | Não listada | LC | Nativo | VAZIO | Não listada (MG) |
| Hoplias malabaricus | 630 | Nao listada | LC | Nativa | VAZIO | Sem lista estadual oficial vigente (MT) |
| Hypomasticus copelandii | 4765 | VAZIO | VAZIO | Nativo | VAZIO | VAZIO |
| Hypomasticus thayeri | 4767 | VU | VU | Nativo | VAZIO | Cr |
| Hypostomus affinis | 4768 | VAZIO | VAZIO | Nativo | VAZIO | VAZIO |
| Knodus moenkhausii | 2 | Não listada | LC | Nativo | VAZIO | Não listada (MG) |
| Oreochromis niloticus | 4771 | VAZIO | VAZIO | Não Nativo | VAZIO | VAZIO |
| Phalloceros uai | 5 | Não listada | LC | Nativo | VAZIO | Não listada (MG) |
| Rhamdia quelen | 450 | Nao listada | LC | Nativa | VAZIO | Sem lista estadual oficial vigente (MT) |

## Decisao pendente no Gate B

- Endemismo vazio em 14/14; ameaca nacional/global vazias em 6/14. Origem preenchida em 14/14.
- Hoplias malabaricus e Rhamdia quelen possuem texto estadual relativo a MT, que nao valida o contexto de MG deste projeto.
- Cadastro incompleto: nao classificar Gate B como nao aplicavel/cadastro completo.
- Proposta para decisao: reutilizar os IDs e atributos atuais exclusivamente nesta carga, mantendo as lacunas registradas e complementando os atributos antes da geracao de resultados, se o usuario aprovar explicitamente a ressalva. Alternativa: completar o cadastro com fonte aprovada antes da carga.
- Nenhuma pesquisa externa ou ampliacao taxonomica executada.

## Restricao tecnica da carga futura

- O sincronizador generico de detalhes reprodutivos apaga detalhes de todas as campanhas do projeto. Nao usa-lo diretamente com um recorte C029.
- A futura carga deve preservar historico e restringir escrita e verificacao de detalhes a C029, com transacao e comparacao fonte x banco.
