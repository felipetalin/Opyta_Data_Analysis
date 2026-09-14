# Validacao

Validadores e auditorias pos-processamento.

Esses scripts devem gerar manifests, inventarios ou relatorios de consistencia.
Quando um validador virar rotina padrao de pipeline, mover a logica para
`src/opyta_analysis` e deixar aqui apenas o entrypoint.

## Validacao Unificada De Migracao

O comando abaixo detecta a planilha de resultados e o cadastro de especies,
executa os validadores oficiais, sincroniza correcoes taxonomicas e gera uma
pasta simples em `VALIDACAO_FINAL/<grupo>` ao lado dos arquivos originais:

```powershell
python scripts\validation\validar_pacote_migracao.py `
  --pasta "G:\caminho\do\projeto\Migracao" `
  --grupo zooplancton
```

Saidas visiveis:

- `RESUMO_VALIDACAO.xlsx`: abrir primeiro;
- `Resultados_FINAL.xlsx`: resultados reconciliados com o cadastro;
- `Cadastro_Especies_FINAL.xlsx`: cadastro final;
- `_lastro/manifesto_validacao.json`: rastreabilidade tecnica.

Perfis iniciais: `zooplancton`, `fitoplancton` e `ictiofauna`. Use `--skip-db` apenas para
testes estruturais sem consulta ao banco.

O perfil `fitoplancton` consulta GBIF, Catalogue of Life e DiatomBase. Para
classificacao, duas bases concordantes definem o valor; sem maioria, vale a base
principal disponivel na ordem DiatomBase, Catalogue of Life e GBIF. Mudancas de
nome exigem concordancia das tres bases. Registros `sp.` e `n.i.` preservam o
nome parcial e recebem apenas a hierarquia ate o menor nivel identificado.

O banco mestre interno participa apenas da conciliacao. Ele nao vota no consenso
taxonomico: registros existentes sao classificados como reutilizar, atualizar,
inserir ou revisar conflito, sempre sem escrita automatica durante a validacao.

Decisoes fornecidas pelo profissional podem ser registradas em
`_lastro/ajustes_profissionais.json`. O arquivo e reaplicado automaticamente em
novas execucoes e fica identificado em `O_QUE_MUDOU`.
