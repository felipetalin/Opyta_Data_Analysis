# Projetos

Fonte principal: [project_registry.json](../registry/project_registry.json).

## Projetos Confirmados No Supabase

| Canonical key | ID | Codigo | Nome Supabase | Status | Lastro |
| --- | ---: | --- | --- | --- | --- |
| `BRAVAL004__diagnostico_biota_aquatica_pder_itambe` | 1 | BRAVAL004 | Diagnóstico biota aquática - PDER Itambé | registered_needs_curation | - |
| `GEOHER001__monitoramento_de_ictio_e_bentos_herculano` | 30 | GEOHER001 | Monitoramento de ictio e bentos - Herculano | active_reference | `outputs/_project_scripts/GEOHER001__monitoramento_de_ictio_e_bentos_herculano` |
| `GEOHER003__diagnostico_ouro_preto` | 31 | GEOHER003 | Diagnóstico Ouro Preto | registered_needs_curation | - |
| `BRAANG01__anglogold` | 115 | BRAANG01 | AngloGold | registered_needs_curation | - |
| `BRACED001__fonseca_biota_aquatica` | 133 | BRACED001 | Fonseca-Biota Aquática | registered_needs_curation | - |
| `BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg` | 9 | BRAAVG002 | Monitoramento de ictio e bentos - Brumado - AVG | reference | `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg` |
| `FERSAM001__sam_metais_diagnostico` | 62 | FERSAM001 | Sam Metais Diagnóstico | reference | `outputs/_project_scripts/FERSAM001__sam_metais_diagnostico` |
| `ITAGUA001__monitoramento_da_fauna` | 165 | ITAGUA001 | Monitoramento da Fauna | reference | `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna` |
| `DUCGEO001__monitoramento_ducal` | 183 | DUCGEO001 | Monitoramento Ducal | reference | `outputs/_project_scripts/DUCGEO001__monitoramento_ducal` |
| `BIOPOR001__monitoramento_da_ictiofauna_da_uhe_porto_estrela` | 186 | BIOPOR001 | Monitoramento da ictiofauna da UHE Porto Estrela | reference | `outputs/_project_scripts/BIOPOR001__monitoramento_da_ictiofauna_da_uhe_porto_estrela` |
| `TOTVAL001__diagnostico_lt_brucutu` | 187 | TOTVAL001 | Diagnóstico LT Brucutu | reference | `outputs/_project_scripts/TOTVAL001__diagnostico_lt_brucutu` |
| `MICGAG001__monitoramento_da_ictiofauna_da_uhe_baguari` | 188 | MICGAG001 | Monitoramento da ictiofauna da UHE Baguari | reference | `outputs/_project_scripts/MICGAG001__monitoramento_da_ictiofauna_da_uhe_baguari` |

## Duplicidades/Pendencias Supabase

| Registro | Situacao | Proxima acao |
| --- | --- | --- |
| `GEOHER003` | Aparece no Supabase como `id_projeto=31` e tambem como `id_projeto=95` com codigo bruto `\u00a0GEOHER003` | Corrigir/confirmar duplicidade antes de usar em analise. |
| Historico antigo de SAM, id 62 | Lastro tecnico antigo | Tratado como `outputs/_project_scripts/FERSAM001__sam_metais_diagnostico__historico_id_62`; confirmar se todo conteudo pertence a SAM. |
| `BRACED001` | Provavel relacao com template Cedro Metais citado em conversas | Criar dossie quando o projeto voltar a ser usado. |
| `TESTE001` | Registro de teste no Supabase | Ignorado pelo registry e pelo auditor de cobertura. |

## Padrao De Dossie

Todo projeto deve ter:

- identidade Supabase;
- entendimento tecnico;
- recorte temporal/espacial;
- decisoes graficas;
- scripts e recipes;
- outputs e lastro;
- aprendizados reutilizaveis.
