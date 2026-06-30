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


def _parse_kml(data: bytes) -> ET.Element:
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        text = data.decode("utf-8", errors="replace")
        if "xsi:" in text and "xmlns:xsi" not in text:
            text = text.replace(
                "<kml ",
                '<kml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ',
                1,
            )
        return ET.fromstring(text)


def _tag_endswith(element: ET.Element, suffix: str) -> bool:
    return str(element.tag).lower().endswith(suffix.lower())


def _child_text(element: ET.Element, tag_suffix: str) -> str:
    for child in element:
        if _tag_endswith(child, tag_suffix):
            return (child.text or "").strip()
    return ""


def read_kml_point_coordinates(path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for data in _read_kml_bytes(path):
        root = _parse_kml(data)
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


def read_kml_line_coordinates(path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    feature_id = 0
    for data in _read_kml_bytes(path):
        root = _parse_kml(data)
        placemarks = [element for element in root.iter() if _tag_endswith(element, "Placemark")]
        for placemark in placemarks:
            name = _child_text(placemark, "name")
            for line in [element for element in placemark.iter() if _tag_endswith(element, "LineString")]:
                coordinates = ""
                for child in line.iter():
                    if _tag_endswith(child, "coordinates"):
                        coordinates = (child.text or "").strip()
                        break
                if not coordinates:
                    continue
                feature_id += 1
                vertex_order = 0
                for token in coordinates.split():
                    parts = token.split(",")
                    if len(parts) < 2:
                        continue
                    try:
                        lon = float(parts[0])
                        lat = float(parts[1])
                    except ValueError:
                        continue
                    rows.append(
                        {
                            "fonte": str(path),
                            "feature_id": feature_id,
                            "nome_feicao": name,
                            "vertex_order": vertex_order,
                            "Longitude": lon,
                            "Latitude": lat,
                        }
                    )
                    vertex_order += 1
    columns = ["fonte", "feature_id", "nome_feicao", "vertex_order", "Longitude", "Latitude"]
    return pd.DataFrame(rows, columns=columns)


def read_kml_polygon_coordinates(path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    polygon_id = 0
    for data in _read_kml_bytes(path):
        root = _parse_kml(data)
        placemarks = [element for element in root.iter() if _tag_endswith(element, "Placemark")]
        for placemark in placemarks:
            name = _child_text(placemark, "name")
            for polygon in [element for element in placemark.iter() if _tag_endswith(element, "Polygon")]:
                polygon_id += 1
                ring_id = 0
                for ring in [element for element in polygon.iter() if _tag_endswith(element, "LinearRing")]:
                    coordinates = ""
                    for child in ring.iter():
                        if _tag_endswith(child, "coordinates"):
                            coordinates = (child.text or "").strip()
                            break
                    if not coordinates:
                        continue
                    ring_id += 1
                    vertex_order = 0
                    for token in coordinates.split():
                        parts = token.split(",")
                        if len(parts) < 2:
                            continue
                        try:
                            lon = float(parts[0])
                            lat = float(parts[1])
                        except ValueError:
                            continue
                        rows.append(
                            {
                                "fonte": str(path),
                                "polygon_id": polygon_id,
                                "ring_id": ring_id,
                                "ring_type": "outer" if ring_id == 1 else "inner",
                                "nome_feicao": name,
                                "vertex_order": vertex_order,
                                "Longitude": lon,
                                "Latitude": lat,
                            }
                        )
                        vertex_order += 1
    columns = [
        "fonte",
        "polygon_id",
        "ring_id",
        "ring_type",
        "nome_feicao",
        "vertex_order",
        "Longitude",
        "Latitude",
    ]
    return pd.DataFrame(rows, columns=columns)
