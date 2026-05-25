"""
Pipeline Meio Físico (fonte: planilhas XLSX locais — padrão Gold Fauna).

Orquestra os 11 scripts de geração em ``scripts/gerar_*.py`` como sub-blocos
de um pipeline único invocável via runner. Os scripts permanecem executáveis
de forma standalone; este módulo apenas configura o ``CLIENT_ROOT`` via
variável de ambiente ``OPYTA_MF_CLIENT_ROOT`` e dispara cada um em sequência.

Diferente de :mod:`opyta_analysis.pipelines.diagnostico.meio_fisico` (que lê
da view Postgres ``fisico_analise_consolidada``), este pipeline lê dos
arquivos locais:

- ``<client_root>/Migração/Físico/Resultados_Meio_Fisico.xlsx``
- ``<client_root>/Migração/Físico/cadastro_parametros_opyta.xlsx``

Configuração por cliente: ``configs/clients/<client>.json`` chave
``meio_fisico_xlsx``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# Ordem canônica dos blocos (cada chave mapeia para o script gerar_*.py).
_BLOCKS: Dict[str, str] = {
    "b2": "gerar_conformidade_sam_etapa2.py",
    "b3": "gerar_b3_grafico_por_parametro.py",
    "b4": "gerar_b4_pct_violacao.py",
    "b5": "gerar_b5_iqa_cetesb.py",
    "b6": "gerar_b6_iet_lamparelli.py",
    "b7": "gerar_b7_iqasb_parcial.py",
    "b8": "gerar_b8_mpelq.py",
    "b9": "gerar_b9_sazonal.py",
    "b11": "gerar_b11_sintese.py",
    "piloto": "gerar_piloto_coliformes_etapa3.py",
    "resumo": "gerar_resumo_tecnico.py",
}

# Conjunto padrão executado quando ``block == 'all'`` (Gold Meio Físico).
# Exclui apenas o piloto (coliformes — análise auxiliar manual).
_DEFAULT_BLOCKS: List[str] = ["b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9", "b11", "resumo"]


@dataclass
class MeioFisicoXlsxConfig:
    """Configuração resolvida do pipeline para um cliente."""
    client_code: str
    client_root: Path
    blocks_default: List[str] = field(default_factory=lambda: list(_DEFAULT_BLOCKS))

    @property
    def src_resultados(self) -> Path:
        return self.client_root / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"

    @property
    def src_cadastro(self) -> Path:
        return self.client_root / "Migração" / "Físico" / "cadastro_parametros_opyta.xlsx"

    @property
    def out_root(self) -> Path:
        return self.client_root / "Resultados" / "Meio_físico"


def _load_client_config(client_code: str, config_root: Optional[Path] = None) -> MeioFisicoXlsxConfig:
    """Carrega ``configs/clients/<client>.json`` e extrai o bloco meio_fisico_xlsx."""
    if config_root is None:
        # subir 3 níveis: <root>/src/opyta_analysis/pipelines/diagnostico/meio_fisico_xlsx.py
        config_root = Path(__file__).resolve().parents[4] / "configs"
    path = config_root / "clients" / f"{client_code.lower()}.json"
    if not path.exists():
        raise FileNotFoundError(f"Config do cliente não encontrada: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    block = data.get("meio_fisico_xlsx")
    if not block or "client_root" not in block:
        raise KeyError(
            f"Bloco 'meio_fisico_xlsx.client_root' ausente em {path.name}"
        )
    return MeioFisicoXlsxConfig(
        client_code=data.get("client_code", client_code),
        client_root=Path(block["client_root"]),
        blocks_default=list(block.get("blocks_default", _DEFAULT_BLOCKS)),
    )


def _resolve_blocks(block: str, default: List[str]) -> List[str]:
    """Resolve seletor de blocos: ``'all'`` | ``'b3,b4'`` | ``'b3'``."""
    if block in ("all", "*", "", None):
        return list(default)
    return [b.strip().lower() for b in str(block).split(",") if b.strip()]


def _run_block(script_name: str, scripts_dir: Path, env: Dict[str, str]) -> int:
    """Executa um script em subprocesso, preservando stdout/stderr no console."""
    script_path = scripts_dir / script_name
    if not script_path.exists():
        print(f"  [AVISO] script ausente: {script_path}")
        return 1
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(scripts_dir.parent),
        env=env,
        check=False,
    )
    return result.returncode


def run_meio_fisico_xlsx_pipeline(
    *,
    client: str = "FERSAM001",
    theme: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
    env_file: Optional[str] = None,
    block: str = "all",
    project_id: int = 0,
    group: str = "meio_fisico_xlsx",
    config_root: Optional[Path] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Executa o pipeline Meio Físico Gold Fauna (fonte XLSX) para o cliente.

    Parameters
    ----------
    client : str
        Código do cliente (deve existir em ``configs/clients/<client>.json``).
    block : str
        ``'all'`` para conjunto padrão, ou lista separada por vírgula
        (ex.: ``'b3,b4'``). Blocos disponíveis: ``b2, b3, b4, b5, b6, b7,
        b8, b9, b11, piloto, resumo``.
    output_dir : Path | None
        Se informado, sobrescreve ``out_root`` derivado de ``client_root``.
        (Atualmente os scripts gravam em ``client_root/Resultados/Meio_físico``;
        este parâmetro é honrado apenas para metadados de execução.)
    """
    cfg = _load_client_config(client, config_root=config_root)
    blocks = _resolve_blocks(block, cfg.blocks_default)

    if not cfg.src_resultados.exists():
        raise FileNotFoundError(
            f"Planilha de resultados não encontrada: {cfg.src_resultados}"
        )

    print(f"[meio_fisico_xlsx] cliente: {cfg.client_code}")
    print(f"[meio_fisico_xlsx] client_root: {cfg.client_root}")
    print(f"[meio_fisico_xlsx] blocos: {blocks}")

    scripts_dir = Path(__file__).resolve().parents[4] / "scripts"

    env = os.environ.copy()
    env["OPYTA_MF_CLIENT_ROOT"] = str(cfg.client_root)

    executed: List[str] = []
    failed: List[str] = []
    for b in blocks:
        script = _BLOCKS.get(b)
        if not script:
            print(f"  [AVISO] bloco desconhecido: {b!r}")
            continue
        print(f"  → bloco {b}: {script}")
        rc = _run_block(script, scripts_dir, env)
        if rc == 0:
            executed.append(b)
        else:
            failed.append(b)
            print(f"  [ERRO] bloco {b} retornou código {rc}")

    out_root = output_dir or cfg.out_root
    generated: List[str] = []
    if out_root.exists():
        for pattern in ("**/*.png", "**/*.xlsx", "**/*.txt"):
            generated.extend(str(p) for p in out_root.glob(pattern))

    print(
        f"[meio_fisico_xlsx] concluído. executados={len(executed)} "
        f"falhas={len(failed)} arquivos={len(generated)}"
    )

    return {
        "project_name": cfg.client_code,
        "rows_loaded": 0,
        "executed_blocks": executed,
        "failed_blocks": failed,
        "campaigns": [],
        "points": [],
        "generated_files": generated,
        "client_root": str(cfg.client_root),
        "output_root": str(out_root),
    }
