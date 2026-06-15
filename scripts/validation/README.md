# Validacao

Validadores e auditorias pos-processamento.

Esses scripts devem gerar manifests, inventarios ou relatorios de consistencia.
Quando um validador virar rotina padrao de pipeline, mover a logica para
`src/opyta_analysis` e deixar aqui apenas o entrypoint.
