"""
Pipeline: Mastofauna — Diagnóstico (EIA/RIMA)
Status: STUB — Implementação pendente (notebooks ainda não disponíveis)

Este módulo cobre análises de mastofauna no contexto de estudos diagnósticos
(duas campanhas: Seca / Chuva).

Não confundir com: pipelines/monitoramento/mastofauna.py
  → Módulo de monitoramento com suporte temporal multi-campanha.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path


def run_mastofauna_pipeline(
    project_id: int,
    group: str,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
) -> Dict[str, Any]:
    """
    Pipeline de diagnóstico para Mastofauna.

    Raises:
        NotImplementedError: Este módulo ainda não foi implementado.
    """
    raise NotImplementedError(
        "Pipeline 'mastofauna' (diagnóstico) ainda não implementado. "
        "Aguardando notebooks de referência."
    )
