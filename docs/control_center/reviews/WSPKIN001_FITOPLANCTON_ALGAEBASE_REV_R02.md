# WSPKIN001 - Fitoplancton - AlgaeBase REV R02

## Controle

- tipo: `taxonomy`
- impacto: `R3`
- estado: `awaiting_revision_approval`
- Gate reaberto: B.
- referencia principal: AlgaeBase.

## Decisao Do Usuario

- limitar o fitoplancton aos filos `Bacillariophyta`, `Charophyta`, `Cyanobacteria`, `Euglenozoa`, `Chlorophyta`, `Ochrophyta`, `Rhodophyta` e `Cryptophyta`.
- padronizar reino e filo segundo a matriz aprovada.
- nao trocar categorias apenas por divergencia entre bases.
- registrar todas as alteracoes na planilha de composicao.

## Dependencias

- cadastro `public.especies` dos 77 taxons usados no projeto;
- 124 linhas de Fitoplancton no consolidado WSPKIN001;
- composicao, tabelas derivadas, graficos, minimapa, sintese, Darwin Core, HTML, manifestos e validacao.

## Execucao

- 77 taxons auditados; 46 tiveram Reino e/ou Filo corrigidos.
- cadastro e 124 linhas consolidadas atualizados com backups transacionais.
- resultado final: exatamente os oito filos aprovados, com zero hierarquias Reino/Filo divergentes.
- composicao definitiva: 77 taxons e quatro abas, incluindo `Decisoes_Taxonomicas` com antes/depois, referencia e decisao.
- cadeia de Fitoplancton regenerada: 14 figuras, tabelas, sintese, minimapa, Darwin Core, HTML, manifesto e validacao.
- validacao final: status `OK`, zero erros; manifesto recalculado e hash da composicao conferido.
- backup de especies: `public.backup_especies_wspkin001_fito_algaebase_r02_20260904t191041z`.
- backup consolidado: `public.backup_biota_wspkin001_fito_algaebase_r02_20260904t191041z`.
- auditoria: `outputs/validacoes/wspkin001_fitoplancton_algaebase_r02_20260904/20260904t191041z_auditoria_fitoplancton_algaebase_r02.json`.
- Gate R: aguarda aprovacao do usuario.
