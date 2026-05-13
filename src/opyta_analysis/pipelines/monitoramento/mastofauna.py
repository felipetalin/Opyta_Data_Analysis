"""
Pipeline: Mastofauna — Monitoramento
Status: EM DESENVOLVIMENTO — Aguardando estrutura do banco de dados

Este módulo implementará análises de mastofauna para projetos de monitoramento
contínuo, com suporte a N campanhas (mensal, trimestral, semestral).

Diferente do diagnóstico (EIA/RIMA), este módulo suporta:
- Comparação temporal entre campanhas
- Análises de tendência e sazonalidade
- Número variável de campanhas por contrato
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path

from .base import MonitoramentoConfig


# ---------------------------------------------------------------------------
# Blocos analíticos previstos (a implementar com base no banco de dados)
# ---------------------------------------------------------------------------
# Bloco A: Composição de espécies por campanha
# Bloco B: Riqueza por campanha (comparativo temporal)
# Bloco C: Abundância / IPA (Índice Pontual de Abundância) por campanha
# Bloco D: Diversidade por campanha (H', J', D)
# Bloco E: Comparação entre campanhas (Beta diversidade)
# Bloco F: [Aguardando análise específica do usuário]
# Bloco G: DarwinCore export
# ---------------------------------------------------------------------------


def run_mastofauna_monitoring_pipeline(
    project_id: int,
    group: str,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
    periodicidade: str = "semestral",
    campanhas_filtro: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Pipeline de monitoramento para Mastofauna.

    Raises:
        NotImplementedError: Implementação em andamento — estrutura do banco
            ainda não foi fornecida para definir os blocos analíticos.
    """
    raise NotImplementedError(
        "Pipeline 'mastofauna' (monitoramento) está em desenvolvimento. "
        "Aguardando definição dos blocos analíticos com base no banco de dados."
    )
