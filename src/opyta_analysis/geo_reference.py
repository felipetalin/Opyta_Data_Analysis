from __future__ import annotations

import re
import zipfile
import math
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd


KML_NS = {"k": "http://www.opengis.net/kml/2.2"}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def standardize_point_name(value: object) -> str:
    text = str(value or "").strip().upper()
    match = re.search(r"\bIC[\s_-]*ARC[\s_-]*(\d+)\b", text)
    if match:
        return f"IC-ARC-{int(match.group(1)):02d}"
    return re.sub(r"\s+", " ", text)


def _read_kml_bytes(path: Path) -> list[bytes]:
    suffix = path.suffix.lower()
    if suffix == ".kmz":
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".kml")]
            if not names:
                raise ValueError(f"Nenhum arquivo KML encontrado no KMZ: {path}")
            return [archive.read(name) for name in names]
    return [path.read_bytes()]


def read_kml_point_coordinates(path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for data in _read_kml_bytes(path):
        root = ET.fromstring(data)
        for placemark in root.findall(".//k:Placemark", KML_NS):
            name = (placemark.findtext("k:name", default="", namespaces=KML_NS) or "").strip()
            coordinates = (placemark.findtext(".//k:Point/k:coordinates", default="", namespaces=KML_NS) or "").strip()
            if not coordinates:
                continue
            first_coord = coordinates.split()[0]
            parts = first_coord.split(",")
            if len(parts) < 2:
                continue
            try:
                lon = float(parts[0])
                lat = float(parts[1])
            except ValueError:
                continue
            rows.append(
                {
                    "Ponto": standardize_point_name(name),
                    "nome_original": name,
                    "Latitude_ref": lat,
                    "Longitude_ref": lon,
                    "fonte_coordenada": str(path),
                }
            )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["Ponto", "nome_original", "Latitude_ref", "Longitude_ref", "fonte_coordenada"])
    return df.drop_duplicates("Ponto", keep="first").sort_values("Ponto").reset_index(drop=True)
