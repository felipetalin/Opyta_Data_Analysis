# Padrao De Nomes

## Fonte De Verdade

A identidade oficial do projeto vem do Supabase:

- tabela: `projetos`;
- codigo: `codigo_interno_opyta`;
- nome: `nome_projeto`;
- id: `id_projeto`.

## Canonical Key

Formato:

```text
SIGLA__nome_do_projeto_no_supabase_slug
```

Exemplo:

```text
GEOHER001__monitoramento_de_ictio_e_bentos_herculano
```

## Onde Usar

| Camada | Regra |
| --- | --- |
| Recipe | `canonical_key` dentro do JSON. |
| Docs | Dossie do projeto deve declarar a `canonical_key`. |
| Scripts | Pastas novas devem usar a `canonical_key` ou alias registrado. |
| Outputs tecnicos | `audit_project_slug` pode ser curto, mas deve constar no registry. |
| Portfolio | Casos devem apontar para `canonical_key`. |

## Compatibilidade

Nomes antigos nao devem ser apagados sem motivo. Eles entram como `aliases` no
registry. Exemplo:

```json
{
  "canonical_key": "GEOHER001__monitoramento_de_ictio_e_bentos_herculano",
  "aliases": ["geoher001_herculano_2022_2025", "geoher001_recorte_2022_2025"]
}
```

## Regra Para Novos Projetos

1. Consultar Supabase.
2. Criar `canonical_key`.
3. Criar dossie em `docs/projects`.
4. Criar recipe em `configs/projects`.
5. Registrar no `docs/registry/project_registry.json`.
