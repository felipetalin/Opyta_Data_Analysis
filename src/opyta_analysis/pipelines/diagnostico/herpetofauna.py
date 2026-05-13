"""
Pipeline: Herpetofauna — Diagnóstico (EIA/RIMA)
Status: STUB — Implementação pendente (notebooks ainda não disponíveis)

Este módulo será implementado assim que os notebooks de referência
para análise de herpetofauna estiverem estruturados.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path


def run_herpetofauna_pipeline(
    project_id: int,
    group: str,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
) -> Dict[str, Any]:
    """
    Pipeline de diagnóstico para Herpetofauna.

    Raises:
        NotImplementedError: Este módulo ainda não foi implementado.
    """
    raise NotImplementedError(
        "Pipeline 'herpetofauna' (diagnóstico) ainda não implementado. "
        "Aguardando notebooks de referência."
    )
