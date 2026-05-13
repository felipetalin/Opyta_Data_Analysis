"""
Módulo: Monitoramento — Base Temporal
Fornece utilitários e tipos comuns para todos os pipelines de monitoramento.

Diferenças-chave vs. Diagnóstico:
- Campanhas variáveis: mensal, trimestral, semestral (N campanhas)
- Análises temporais específicas: tendências, sazonalidade, autocorrelação
- Comparação entre campanhas (não só Seca/Chuva)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class MonitoramentoCampanha:
    """Representa uma campanha de monitoramento."""
    nome: str           # ex: "Campanha 1", "Jan/2025", "Seca 2025"
    data_coleta: str    # ISO date ou label livre
    ordem: int          # Ordem cronológica para plots temporais


@dataclass
class MonitoramentoConfig:
    """Configuração base para pipelines de monitoramento."""
    project_id: int
    group: str
    theme: Dict[str, Any]
    output_dir: Path
    env_file: Optional[str] = None
    block: str = "all"
    periodicidade: str = "semestral"  # mensal | trimestral | semestral
    campanhas_filtro: Optional[List[str]] = field(default=None)
    """Se None, usa todas as campanhas disponíveis no projeto."""
