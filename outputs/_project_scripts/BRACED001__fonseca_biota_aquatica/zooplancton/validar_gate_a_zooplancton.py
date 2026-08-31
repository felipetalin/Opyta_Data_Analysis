from __future__ import annotations

import argparse
import math
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.braaeg001 import validar_nova_base_biota as validator


PROJECT_CODE = "BRACED001"
GROUP = "Zooplancton"


def normalize_point(value: object) -> str:
    return str(value).strip().casefold()


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_008.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_m * math.asin(math.sqrt(a))


def read_kml_points(path: Path) -> dict[str, tuple[str, float, float]]:
    root = ET.parse(path).getroot()
    namespace = {"k": "http://www.opengis.net/kml/2.2"}
    points: dict[str, tuple[str, float, float]] = {}
    for placemark in root.findall(".//k:Placemark", namespace):
        name = placemark.findtext("k:name", default="", namespaces=namespace).strip()
        coordinates = placemark.findtext(".//k:Point/k:coordinates", default="", namespaces=namespace).strip()
        if not name or not coordinates:
            continue
        longitude, latitude, *_ = coordinates.split(",")
        points[normalize_point(name)] = (name, float(latitude), float(longitude))
    return points


def add_spatial_audit(bundle: validator.ValidationBundle, workbook: validator.GroupWorkbook, reference: Path, tolerance_m: float) -> None:
    rows: list[dict[str, object]] = []
    reference_points = read_kml_points(reference)
    source = workbook.sheets.get("Pontos_e_Campanhas", pd.DataFrame())

    if not reference_points:
        bundle.issues.append(
            validator.Issue("Gate A", GROUP, "block", "COORDINATE_REFERENCE_EMPTY", "A referencia KML nao contem pontos legiveis.")
        )
        return

    for _, row in source.iterrows():
        point = str(row.get("Ponto", "")).strip()
        campaign = str(row.get("Campanha", "")).strip()
        key = normalize_point(point)
        reference_row = reference_points.get(key)
        if reference_row is None:
            rows.append({"ponto": point, "campanha": campaign, "status": "missing_reference"})
            continue
        ref_name, ref_lat, ref_lon = reference_row
        try:
            source_lat = float(row.get("Latitude"))
            source_lon = float(row.get("Longitude"))
            distance_m = haversine_m(source_lat, source_lon, ref_lat, ref_lon)
        except (TypeError, ValueError):
            distance_m = None
        status = "same" if distance_m is not None and distance_m <= tolerance_m else "divergent"
        rows.append(
            {
                "ponto": point,
                "campanha": campaign,
                "ponto_referencia": ref_name,
                "latitude_fonte": row.get("Latitude"),
                "longitude_fonte": row.get("Longitude"),
                "latitude_referencia": ref_lat,
                "longitude_referencia": ref_lon,
                "distancia_m": distance_m,
                "tolerancia_m": tolerance_m,
                "status": status,
            }
        )

    bundle.course_comparison.extend(rows)
    missing = [row for row in rows if row["status"] == "missing_reference"]
    divergent = [row for row in rows if row["status"] == "divergent"]
    if missing:
        bundle.issues.append(
            validator.Issue(
                "Gate A",
                GROUP,
                "block",
                "POINT_WITHOUT_COORDINATE_REFERENCE",
                "Ha pontos da planilha sem correspondencia na referencia KML.",
                detail=", ".join(sorted({str(row["ponto"]) for row in missing})),
                row_count=len(missing),
            )
        )
    if divergent:
        bundle.issues.append(
            validator.Issue(
                "Gate A",
                GROUP,
                "block",
                "COORDINATE_DISTANCE_EXCEEDS_TOLERANCE",
                f"Ha coordenadas com distancia superior a {tolerance_m:g} m da referencia KML.",
                detail=", ".join(sorted({str(row["ponto"]) for row in divergent})),
                row_count=len(divergent),
            )
        )


def main() -> int:
    global GROUP
    parser = argparse.ArgumentParser(description="Validate BRACED001 bioaquatic data for Control Center Gate A.")
    parser.add_argument("--input-file", required=True, type=Path)
    parser.add_argument("--group", default=GROUP)
    parser.add_argument("--output-prefix", default="validacao_gate_a_zooplancton_braced001")
    parser.add_argument("--coordinate-reference", required=True, type=Path)
    parser.add_argument("--coordinate-tolerance-m", type=float, default=50.0)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--opyta-data-root", type=Path, default=Path.cwd().parent / "Opyta_Data")
    args = parser.parse_args()
    GROUP = args.group

    if not args.input_file.exists():
        raise FileNotFoundError(args.input_file)
    if not args.coordinate_reference.exists():
        raise FileNotFoundError(args.coordinate_reference)

    original_loader = validator.load_workbooks
    discovered = original_loader(args.input_file.parent)
    selected = [wb for wb in discovered if wb.path.resolve() == args.input_file.resolve()]
    if len(selected) != 1:
        raise RuntimeError(f"Expected one zooplankton workbook, found {len(selected)}: {args.input_file}")

    validator.PROJECT_CODE = PROJECT_CODE
    validator.EXPECTED_CODE = PROJECT_CODE
    validator.CANONICAL_GROUPS = [GROUP]
    validator.load_workbooks = lambda _input_dir: selected

    bundle = validator.build_report(
        input_dir=args.input_file.parent,
        meio_fisico_file=None,
        opyta_data_root=args.opyta_data_root,
        no_db=True,
        allow_uneven_campaigns=False,
        campaign_coverage_note=None,
    )
    add_spatial_audit(bundle, selected[0], args.coordinate_reference, args.coordinate_tolerance_m)
    gate_a_findings = [issue for issue in bundle.issues if issue.gate == "Gate A"]
    bundle.status_gate_a = (
        "BLOCKED"
        if any(issue.severity == "block" for issue in gate_a_findings)
        else "PASS_WITH_WARNINGS"
        if gate_a_findings
        else "PASS"
    )
    bundle.status_gate_b = "NOT_RUN"

    json_path, xlsx_path = validator.write_outputs(bundle, args.output_dir, None)
    stamp = datetime.fromisoformat(bundle.generated_at).strftime("%Y%m%dT%H%M%S")
    target_base = f"{stamp}_{args.output_prefix}"
    target_json = json_path.with_name(f"{target_base}.json")
    target_xlsx = xlsx_path.with_name(f"{target_base}.xlsx")
    json_path.replace(target_json)
    xlsx_path.replace(target_xlsx)

    print(f"status_gate_a={bundle.status_gate_a}")
    print(f"bloqueios={sum(issue.severity == 'block' and issue.gate == 'Gate A' for issue in bundle.issues)}")
    print(f"avisos={sum(issue.severity == 'warning' and issue.gate == 'Gate A' for issue in bundle.issues)}")
    print(f"json={target_json}")
    print(f"xlsx={target_xlsx}")
    return 1 if bundle.status_gate_a == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
