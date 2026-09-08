"""Regressao para o incidente ITAGUA001/Ictiofauna/C029: rodar uma campanha
nao pode apagar, sobrescrever ou reutilizar silenciosamente o diretorio de
auditoria de outra campanha/empreendimento.

Contexto: `runner._get_project_audit_dir` (renomeada para
`_get_project_group_dir`) identificava a trilha de auditoria so por
(projeto, grupo). `_prune_timestamped_audit_artifacts` apagava os arquivos
timestampados de qualquer execucao anterior do MESMO projeto+grupo, mesmo
que fosse de outra campanha ou empreendimento. Isso apagou o lastro da C028
(ITAGUA001/Ictiofauna) ao gerar uma amostra da C029 do mesmo projeto+grupo.

Estes testes chamam diretamente as funcoes internas de trilha de auditoria
do runner (sem tocar o Supabase) para provar que:
1. C028 e C029 do mesmo projeto+grupo coexistem sem se apagarem.
2. Duas execucoes consecutivas da C029 tambem coexistem sem se apagarem.
3. O ponteiro "latest" usado por `opyta_analysis.fauna.audit.audit_project`
   continua no mesmo caminho de sempre (contrato preservado).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from opyta_analysis import runner as runner_mod
from opyta_analysis.config import RunParams
from opyta_analysis.fauna.audit import audit_project


def _make_params(tmp_output: Path, *, campaigns, pch_target) -> RunParams:
    return RunParams(
        project_id=165,
        group="Ictiofauna",
        pipeline="ictio_partial",
        client="itagua001_guanhaes",
        output_dir=tmp_output,
        env_file=None,
        block="all",
        audit_project_slug="ITAGUA001__monitoramento_da_fauna",
        campaigns=campaigns,
        pch_target=pch_target,
    )


def _make_result(rows_loaded: int, generated_files: list[str]) -> dict:
    return {
        "status": "ok",
        "pipeline": "ictio_partial",
        "details": {
            "rows_loaded": rows_loaded,
            "executed_blocks": ["6.1"],
            "campaigns": [],
            "points": [],
            "generated_files": generated_files,
            "warnings": [],
        },
    }


def _write_audit_trail(config_root: Path, params: RunParams, result: dict, run_id: str) -> dict:
    """Espelha exatamente o trecho de `runner.run()` que grava a trilha de
    auditoria, sem executar nenhum pipeline real nem tocar o Supabase."""
    details = result["details"]
    group_dir = runner_mod._get_project_group_dir(params, config_root, details)
    run_dir = runner_mod._get_execution_run_dir(group_dir, params, details, run_id)
    metadata_path = runner_mod._generate_execution_metadata(params, result, config_root, group_dir, run_dir, run_id)
    reproducer_path = runner_mod._generate_reproducer_script(params, config_root, group_dir, run_dir, run_id)
    return {"group_dir": group_dir, "run_dir": run_dir, "metadata_path": Path(metadata_path), "reproducer_path": Path(reproducer_path)}


@pytest.fixture
def config_root(tmp_path: Path) -> Path:
    root = tmp_path / "configs"
    root.mkdir()
    return root


def test_c028_and_c029_coexist_without_deleting_each_other(config_root: Path, tmp_path: Path):
    params_c028 = _make_params(tmp_path / "out_c028_spt", campaigns=["C028-2026-05-SC"], pch_target="Senhora do Porto")
    result_c028 = _make_result(rows_loaded=11, generated_files=["c028_arquivo_a.xlsx", "c028_arquivo_b.png"])
    trail_c028 = _write_audit_trail(config_root, params_c028, result_c028, run_id="20260526T155411Z")

    assert trail_c028["run_dir"].exists()
    assert trail_c028["metadata_path"].exists()
    assert trail_c028["reproducer_path"].exists()
    c028_metadata_before = json.loads(trail_c028["metadata_path"].read_text(encoding="utf-8"))
    assert c028_metadata_before["rows_loaded"] == 11

    # Agora roda a C029 do MESMO projeto+grupo+empreendimento.
    params_c029 = _make_params(tmp_path / "out_c029_spt", campaigns=["C029-2026-08-SC"], pch_target="Senhora do Porto")
    result_c029 = _make_result(rows_loaded=24, generated_files=["c029_arquivo_a.xlsx"])
    trail_c029 = _write_audit_trail(config_root, params_c029, result_c029, run_id="20260908T173822Z")

    # O diretorio imutavel da C028 continua existindo, intacto.
    assert trail_c028["run_dir"].exists(), "diretorio de execucao da C028 foi removido pela C029"
    assert trail_c028["metadata_path"].exists(), "metadata da C028 foi removida pela C029"
    assert trail_c028["reproducer_path"].exists(), "reprodutor da C028 foi removido pela C029"
    c028_metadata_after = json.loads(trail_c028["metadata_path"].read_text(encoding="utf-8"))
    assert c028_metadata_after == c028_metadata_before, "metadata da C028 foi sobrescrita pela C029"

    # C028 e C029 tem diretorios de execucao DIFERENTES (identidades distintas).
    assert trail_c028["run_dir"] != trail_c029["run_dir"]
    assert "c028" in str(trail_c028["run_dir"]).lower()
    assert "c029" in str(trail_c029["run_dir"]).lower()

    # As duas ficam sob o mesmo (projeto, grupo) — mesmo "group_dir".
    assert trail_c028["group_dir"] == trail_c029["group_dir"]

    # O ponteiro "latest" no group_dir reflete a execucao mais recente (C029) —
    # isso e o comportamento ESPERADO de um ponteiro de conveniencia, e nao
    # remove o historico imutavel de C028 (ja verificado acima).
    latest_metadata = json.loads((trail_c029["group_dir"] / "execution_metadata.json").read_text(encoding="utf-8"))
    assert latest_metadata["rows_loaded"] == 24


def test_two_consecutive_c029_runs_preserve_previous_run(config_root: Path, tmp_path: Path):
    params = _make_params(tmp_path / "out_c029_spt", campaigns=["C029-2026-08-SC"], pch_target="Senhora do Porto")

    result_run1 = _make_result(rows_loaded=24, generated_files=["6_1_tabela_especies_senhora_do_porto.xlsx"])
    trail_run1 = _write_audit_trail(config_root, params, result_run1, run_id="20260908T173323Z")

    result_run2 = _make_result(rows_loaded=24, generated_files=["6_1_tabela_especies_senhora_do_porto.xlsx"])
    trail_run2 = _write_audit_trail(config_root, params, result_run2, run_id="20260908T173822Z")

    # Cada execucao tem seu proprio diretorio imutavel, mesmo com identidade
    # (campanha+empreendimento) identica.
    assert trail_run1["run_dir"] != trail_run2["run_dir"]
    assert trail_run1["run_dir"].exists(), "primeira execucao da C029 foi apagada pela segunda"
    assert trail_run1["metadata_path"].exists(), "metadata da primeira execucao da C029 foi apagada"
    assert trail_run1["reproducer_path"].exists(), "reprodutor da primeira execucao da C029 foi apagado"
    assert trail_run2["run_dir"].exists()

    # Nenhum arquivo extra sobra nem falta: as duas pastas "runs/<identidade>/<run_id>"
    # coexistem como irmãs dentro do mesmo diretorio de identidade.
    identity_dir = trail_run1["run_dir"].parent
    assert identity_dir == trail_run2["run_dir"].parent
    run_subdirs = sorted(p.name for p in identity_dir.iterdir() if p.is_dir())
    assert run_subdirs == ["20260908T173323Z", "20260908T173822Z"]


def test_group_dir_latest_pointer_keeps_audit_project_contract(config_root: Path, tmp_path: Path):
    """`audit_project()` descobre metadados com `project_dir.glob("*/execution_metadata.json")`
    (um unico nivel). Essa correcao NAO pode mudar esse caminho."""
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    generated_file = output_dir / "6_1_tabela_especies_senhora_do_porto.xlsx"
    generated_file.write_bytes(b"fake-xlsx")

    params = _make_params(output_dir, campaigns=["C029-2026-08-SC"], pch_target="Senhora do Porto")
    result = _make_result(rows_loaded=24, generated_files=[str(generated_file)])
    trail = _write_audit_trail(config_root, params, result, run_id="20260908T173822Z")

    latest_metadata_path = trail["group_dir"] / "execution_metadata.json"
    assert latest_metadata_path.exists()

    project_dir = trail["group_dir"].parent  # outputs/_project_scripts/<project_slug>/
    found_via_glob = sorted(project_dir.glob("*/execution_metadata.json"))
    assert latest_metadata_path in found_via_glob, (
        "o ponteiro 'latest' mudou de lugar; audit_project() deixaria de encontra-lo"
    )

    manifest = audit_project(project_dir)
    assert manifest["summary"]["groups_count"] == 1
    assert manifest["errors"] == [], f"discovery via audit_project() nao deveria falhar: {manifest['errors']}"


def test_different_pch_same_campaign_do_not_collide(config_root: Path, tmp_path: Path):
    params_spt = _make_params(tmp_path / "out_spt", campaigns=["C029-2026-08-SC"], pch_target="Senhora do Porto")
    params_jac = _make_params(tmp_path / "out_jac", campaigns=["C029-2026-08-SC"], pch_target="Jacaré")

    trail_spt = _write_audit_trail(config_root, params_spt, _make_result(24, []), run_id="20260908T173322Z")
    trail_jac = _write_audit_trail(config_root, params_jac, _make_result(93, []), run_id="20260908T173323Z")

    assert trail_spt["run_dir"] != trail_jac["run_dir"]
    assert trail_spt["run_dir"].exists()
    assert trail_jac["run_dir"].exists()
    assert json.loads(trail_spt["metadata_path"].read_text(encoding="utf-8"))["rows_loaded"] == 24


def test_no_recursive_delete_helpers_in_runner_module():
    """Guarda contra reintroducao de exclusao recursiva/poda destrutiva no
    modulo de auditoria do runner."""
    source = Path(runner_mod.__file__).read_text(encoding="utf-8")
    assert "shutil.rmtree" not in source
    assert ".unlink(" not in source
    assert "_prune_timestamped_audit_artifacts" not in source
