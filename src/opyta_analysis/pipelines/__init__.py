# --- Diagnóstico (EIA/RIMA) ---
from .diagnostico import (
    run_meio_fisico_pipeline,
    run_zoobentos_pipeline,
    run_fitoplancton_pipeline,
    run_zooplancton_pipeline,
    run_ictio_pipeline,
    run_macrofitas_pipeline,
    run_mastofauna_pipeline,
    run_primatas_pipeline,
    run_herpetofauna_pipeline,
    run_avifauna_pipeline,
)

# --- Monitoramento (multi-campanha) ---
from .monitoramento import (
    run_mastofauna_monitoring_pipeline,
)

__all__ = [
    # Diagnóstico
    "run_zoobentos_pipeline",
    "run_fitoplancton_pipeline",
    "run_zooplancton_pipeline",
    "run_ictio_pipeline",
    "run_macrofitas_pipeline",
    "run_mastofauna_pipeline",
    "run_primatas_pipeline",
    "run_herpetofauna_pipeline",
    "run_avifauna_pipeline",
    "run_meio_fisico_pipeline",
    # Monitoramento
    "run_mastofauna_monitoring_pipeline",
]
