from .zoobentos import run_zoobentos_pipeline
from .fitoplancton import run_fitoplancton_pipeline
from .zooplancton import run_zooplancton_pipeline
from .ictio import run_ictio_pipeline
from .macrofitas import run_macrofitas_pipeline
from .mastofauna import run_mastofauna_pipeline
from .herpetofauna import run_herpetofauna_pipeline
from .avifauna import run_avifauna_pipeline

__all__ = [
    "run_zoobentos_pipeline",
    "run_fitoplancton_pipeline",
    "run_zooplancton_pipeline",
    "run_ictio_pipeline",
    "run_macrofitas_pipeline",
    "run_mastofauna_pipeline",
    "run_herpetofauna_pipeline",
    "run_avifauna_pipeline",
]
