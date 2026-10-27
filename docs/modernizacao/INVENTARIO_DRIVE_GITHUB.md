# Inventário parcial Drive × GitHub

Data da inspeção: 2026-10-27 (America/Sao_Paulo).
Base GitHub: b2fcf2a9ce383188f96c4429b768f82bc62fda5c,
branch modernizacao/memoria-e-auditoria-inicial.
Escopo: evidências selecionadas, não inventário completo.

## Fontes localizadas
- [Opyta_Data_Analysis](https://drive.google.com/drive/folders/1ZD4kzzrznP2bbPkcjTcjfHk7Nj_O9ttv).
- [Opyta_Data](https://drive.google.com/drive/folders/15EUr3YuZYLWCuUhAFCZqup-g-VpcS5S2).
- [Worktrees](https://drive.google.com/drive/folders/1LsVLqiTCGH7i4_tehEVHlbYuoeQ1f6hC): subpasta o-que-e-isso-explained localizada; conteúdo ainda não comparado.

## Documentos
| Caminho relativo ao Analysis | Fonte Drive | Resultado frente ao GitHub examinado |
| --- | --- | --- |
| AGENTS.md | [arquivo](https://drive.google.com/file/d/1fW8i7p2S5ZgPAjvrex3-n4hjdaWB6RT-/view) | Conteúdo diferente: Drive contém instruções de outubro para Darwin Core e contexto seletivo; GitHub tinha instruções anteriores. |
| docs/control_center/README.md | [arquivo](https://drive.google.com/file/d/13zHwjAiNwcT-ha1kKv9Z9CBedK2cpM13/view) | Conteúdo diferente: Drive roteia por tipo de tarefa; GitHub examinado aciona fluxo completo. |
| docs/control_center/LLM_CONTEXT_POLICY.md | [arquivo](https://drive.google.com/file/d/1-0qwFd3u9yEWMj-AERgmRod7GFWJg9De/view) | Drive lido; GitHub retornou 404 no caminho equivalente. Não comprova ausência em toda branch/repositório. |
| docs/AUDITORIA_CONHECIMENTO_MIGRACAO_VALIDACAO.md | [arquivo](https://drive.google.com/file/d/1Sjiyv6wSIqctUQM9tXrXtjWTbkHIgP_s/view) | Drive lido; GitHub retornou 404 no caminho equivalente. Conclusões técnicas históricas ainda precisam ser conferidas no código. |
| docs/control_center/LEARNING_SYSTEM.md | [arquivo](https://drive.google.com/file/d/1hvb5xuvf8VSjzqib-T2Sn-ZYaKUr7rzb/view) | Drive lido; tipos de memória e promoção para patterns/código já descritos. Não comparado por conteúdo com GitHub nesta rodada. |
| docs/decisions/2026-07-06_opyta_data_backend_orquestrador.md | [arquivo](https://drive.google.com/file/d/1gGmFD-XmqZPwOhykfxvokxaUJVCwCzC7/view) | Drive lido; direção de arquitetura registrada com especificação pendente. Não prova implementação. |

## Primeiro recorte de código
Download autenticado dos arquivos completos; leitura de GitHub no SHA acima.
Comparação textual normalizada: UTF-8 sem BOM e CRLF convertidos em LF.
Hashes SHA-256 completos abaixo permitem reproduzir a comparação. Não se executou o código.

| Caminho | Drive | Blob GitHub | Resultado |
| --- | --- | --- | --- |
| src/opyta_analysis/runner.py | [arquivo](https://drive.google.com/file/d/1ZopxoQLl8pa-YgAohfskY41uXRhdvNwn/view) | 1edc18829cd60c12b2645d7713f1b1b3e3a625fa | Diferente após normalização; 5 linhas de adição/remoção no diff textual, sem contar cabeçalhos. Impacto pendente. |
| src/opyta_analysis/supabase_client.py | [arquivo](https://drive.google.com/file/d/1_gwvujRVGvcFqEub6NbmNiTC8aRklQ_a/view) | 75b44dd548b2ff9b91431d43793913e86a086a19 | Diferente após normalização; 4 linhas de adição/remoção no diff textual, sem contar cabeçalhos. Impacto pendente. |

### runner.py
- Drive original: 775fcd072fa6179e4f1160e630e5c5bd9d5f6955c73f5c513116782ef27a4f72
- Drive normalizado: 2bc2a0b14fb6beb6f9e95fd1cf8010aee1b942e0d7d96c35a1bc44e741a302df
- GitHub normalizado: 9ab0005e670a7fa1966f68ea85fe7ff2b9b84535371d265004cb2d9f0f023cb8

### supabase_client.py
- Drive original: 507bfdaade396d826b9115cfa9ce48c99055b140122c114047e9ac9e088cde44
- Drive normalizado: 985a19efe5cb707eedf98ec1256b2e13ac9656c693c258d945b9f5490e39c4b1
- GitHub normalizado: 84627689da0a1e64f32a1e6d144efa88ea118eaee9fd12a0cd1472475d9d724b

## Limitações e aprendizados da inspeção
- Busca do conector omitiu .py em uma listagem; leitura direta da pasta exibiu os arquivos. Usar leitura/listagem direta para o inventário de código.
- Fetch textual dos .py devolveu string vazia; o conteúdo bruto obtido por download foi usado na comparação. Vazio textual não significa arquivo vazio.
- Datas e tamanhos são metadados de descoberta; não provam qual versão é correta.
- GitHub não representa necessariamente o trabalho integral do Drive; Drive não é automaticamente a versão aprovada de cada módulo.
- Nenhuma sincronização ou seleção de versão vencedora foi realizada.

## Próximo recorte
Análise semântica dos dois diffs; entry points/pipelines, contratos de validação,
configurações/recipes e dependências. Usar este inventário para evitar repetir a descoberta.
