# BRAAEG001 - Ictiofauna - Escopo Gate C

## Referencia

Padrao de diagnostico curto baseado em FERSAM001/VIRITA001:

- barras agrupadas por campanha para riqueza, abundancia, CPUEn e CPUEb;
- painel unico de diversidade alfa;
- paleta verde FERSAM001;
- layout Gold horizontal `15 x 10`, 600 dpi;
- tabela completa de distribuicao suficiente para uma ou duas campanhas;
- sinteses multicampanha de serie longa desativadas.

## Recorte

- Projeto: `BRAAEG001`
- Grupo: `Ictiofauna`
- Campanhas: `C001-2026-02-CH` e `C002-2026-06-SC`
- Pontos: `PT_01` a `PT_12`
- Base migrada: `biota_analise_consolidada`, `id_projeto=195`
- Biomassa/CPUEb: usar planilha linha-a-linha validada em `lastros_migracao/Resultados_Migração _Ictio.xlsx`

## Analises Diagnosticas Pertinentes

1. Composicao e atributos das especies
   - tabela de composicao taxonomica;
   - ocorrencia por campanha e ponto;
   - atributos ecologicos disponiveis no cadastro: origem, ameaca, endemismo, habito alimentar, guilda, migratorio, raridade e sensibilidade ambiental.

2. Distribuicao ponto x campanha
   - tabela completa de distribuicao;
   - ocorrencia por ponto e campanha;
   - sem sintese multicampanha extra, pois o recorte tem duas campanhas.

3. Riqueza e abundancia
   - riqueza por ponto e campanha;
   - abundancia por ponto e campanha;
   - figuras em barras agrupadas.

4. Composicao taxonomica superior
   - riqueza por ordem;
   - riqueza por familia;
   - barras e roscas taxonomicas, se houver categorias suficientes.

5. Esforco e captura por unidade de esforco
   - CPUEn por ponto;
   - CPUEb por ponto;
   - CPUEn por especie;
   - CPUEb por especie;
   - versoes por especie x ponto quando legiveis.

6. Biometria e biomassa
   - resumo por especie;
   - numero de individuos;
   - CP medio, minimo e maximo;
   - peso corporal medio, minimo e maximo;
   - biomassa total por especie.

7. Diversidade alfa
   - Shannon H;
   - Pielou J;
   - base quantitativa: CPUEn;
   - interpretacao com ressalva por baixa riqueza total.

8. Similaridade
   - matriz de comunidade por CPUEn;
   - Bray-Curtis entre pontos;
   - dendrograma apenas como apoio descritivo, sem inferencia estatistica.

9. Suficiencia amostral
   - riqueza observada;
   - Jackknife 1;
   - curva do coletor exploratoria.

10. Entrega e rastreabilidade
   - planilhas XLSX;
   - figuras PNG;
   - relatorio HTML tecnico simples;
   - manifesto com arquivos e hashes.

## Fora Do Escopo Nesta Rodada

- NMDS;
- PERMANOVA;
- diversidade beta formal;
- LCBD;
- analise funcional complexa;
- tendencias temporais;
- mapas ou analises espaciais avancadas;
- inferencia estatistica forte.

## Pendencia Gate C

Confirmar com o usuario:

- template diagnostico curto FERSAM001/VIRITA001;
- paleta verde FERSAM001;
- pasta de saida `ictiofauna`;
- lista de produtos acima.
