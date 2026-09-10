# Diretriz De Identidade Supabase

## Objetivo

Evitar que a ausência temporária de `id_projeto` no registry local interrompa ou seja reaberta como pendência nas etapas de validação, taxonomia, consolidação local e configuração de análises.

## Regra Operacional

Na abertura, consultar obrigatoriamente o Supabase por `codigo_interno_opyta`. Quando o projeto existir, registrar seu `id_projeto` no registry local. Quando não existir e houver autorização do usuário, criar o cliente/projeto no Supabase e registrar o ID retornado.

`codigo_interno_opyta` e `canonical_key` permitem manter a operação identificada entre etapas, mas não substituem essa consulta obrigatória ao Supabase. O preflight imediatamente anterior à migração apenas reconfirma a identidade já resolvida, evitando carga em projeto incorreto.

## Não Reabrir Como Pendência

Não solicitar nem registrar novamente a falta de `id_projeto` em validação dos dados, Gate A, cadastro e auditoria de espécies, Gate B, preparação, consolidação local ou configuração de análises **depois** da consulta obrigatória de abertura já ter sido executada e registrada.

## Preflight De Migração

Antes da primeira carga, reconfirmar o projeto por `codigo_interno_opyta` e o `id_projeto` já registrado, e bloquear a carga somente por ausência, ambiguidade ou conflito. O resultado da consulta de abertura é reutilizável nas operações futuras; não reabrir uma pendência já resolvida sem evidência de alteração no Supabase.

## Aplicação Ao WSPKIN001

WSPKIN001 está cadastrado localmente como `WSPKIN001__kinross_bandeirinhas` e no Supabase como `id_projeto=211`. Não é pendência de Gate A ou Gate B.
