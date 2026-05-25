# Meio Físico Gold - Memória Operacional

Atualizado em 2026-05-25 para SAM Metais / FERSAM001.

## Regras que não podem se perder

- A unidade dos dados é autoritativa. O VMP do cadastro deve ser convertido para a unidade reportada nos resultados antes de plotar ou julgar violação.
- Filtrar VMP ausente, `-`, `NA` e valores `<= 0`, exceto `VMP=0` em parâmetros microbiológicos de ausência (`Coliformes`, `Escherichia coli`/`E. coli`).
- Água Superficial usa CONAMA 357 Classe 2 como referência operacional do diagnóstico.
- Em Água Superficial, avaliar limites mínimos e máximos:
  - `VMP_357_Cl2_Min` viola quando `valor < limite_min`.
  - `VMP_357_Cl2_Max` viola quando `valor > limite_max`.
  - pH é faixa 6-9.
  - OD viola por mínimo de 5 mg/L.
- Amônia em Água Superficial é dinâmica por pH no mesmo ponto/campanha.
- Resultado com sinal `<` ou `<=` não deve ser contado como violação.
- Se o Excel/Drive bloquear o arquivo oficial, salvar `_NEW` e fazer os blocos seguintes lerem a versão mais recente entre oficial e `_NEW`.
- IET Lamparelli para reservatórios usa fósforo total e clorofila-a em µg/L (equivalente a mg/m3). Se Fósforo Total vier em mg/L na fonte, converter para µg/L multiplicando por 1000 antes de calcular `IET_PT`.

## Aprendizado do erro de 2026-05-25

O `04_Pct_Violacao.xlsx` de Superficial estava subcontando violações porque o B4 usava apenas `VMP_357_Cl2_Max` e a regra `valor > limite`. Isso ignora parâmetros com limite mínimo, principalmente Oxigênio Dissolvido In Situ. A correção foi transformar os VMPs em regras explícitas `min`/`max`, gravar `Limite_Min`, `Limite_Max` e `Regra_VMP`, e alinhar a tabela de conformidade B2 para marcar somente Classe 2 em Superficial.

Resultado validado: 8 parâmetros violados em Superficial:

- Ferro Dissolvido
- Coliformes Termotolerantes por tubos múltiplos - NMP
- Alumínio Dissolvido
- pH In Situ
- Oxigênio Dissolvido In Situ
- Manganês Dissolvido
- Escherichia coli por tubos múltiplos (substrato enzimático) - NMP
- Fósforo Total

Na revisão de Subterrânea, a divergência entre B2 e B4 vinha do filtro `VMP <= 0`: ele removia corretamente placeholders como Arsênio/Irrigação, mas também removia o padrão microbiológico de ausência (`VMP=0`) para Coliformes e E. coli. A regra correta é manter `VMP=0` apenas para parâmetros microbiológicos de ausência e continuar descartando zero nos demais parâmetros.

Resultado validado em Subterrânea: 5 parâmetros violados:

- Ferro Total
- Manganês Total
- Coliformes Termotolerantes por tubos múltiplos - NMP
- Alumínio Total
- Escherichia coli por tubos múltiplos (substrato enzimático) – NMP

## Sinais de alerta

- Turbidez aparecendo como violação em Superficial pode indicar uso indevido de Classe 1, pois Classe 2 aceita até 100 NTU.
- Clorofila A com 100% ou valor muito alto pode indicar conversão de unidade ausente entre mg/L e µg/L.
- OD ausente do B4 quando aparece na conformidade indica que limites mínimos não estão sendo avaliados.
- Divergência entre `01_Conformidade` e `04_Pct_Violacao` normalmente significa diferença de regra, não necessariamente dado novo.
- Em Subterrânea, divergência envolvendo Coliformes/E. coli pode indicar que `VMP=0` foi tratado como placeholder em vez de padrão de ausência.
- IET todo Ultraoligotrófico/baixo demais com fósforo em mg/L é sinal clássico de ausência de conversão mg/L -> µg/L no `IET_PT`.
