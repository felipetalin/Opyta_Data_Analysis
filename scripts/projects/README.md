# Scripts Por Projeto

Scripts nesta pasta pertencem a um cliente/projeto especifico e ainda nao foram
transformados em pipeline generico ou recipe.

Regra pratica:

- se o script depende de caminhos, nomes de campanha ou decisoes de um projeto,
  fica aqui;
- se o padrao se repetir em outro projeto, a logica deve migrar para
  `src/opyta_analysis`;
- se for uma execucao reprodutivel, criar tambem uma recipe em
  `configs/projects/`.
