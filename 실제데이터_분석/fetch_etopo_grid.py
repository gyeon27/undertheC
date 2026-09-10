# -*- coding: utf-8 -*-
"""NOAA ETOPO 2022 bed elevation을 규칙 격자로 내려받는다.

ArcGIS ImageServer의 exportImage를 사용하므로 지점마다 수천 번 요청하지 않고,
한 번의 요청으로 분석 영역 전체를 같은 해상도로 받을 수 있다.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


SERVICE = (
    "https://gis.ngdc.noaa.gov/arcgis/rest/services/"
    "DEM_mosaics/DEM_all/ImageServer"
)
ETOPO_BED_RASTER_ID = 2530
SOURCE_NAME = "ETOPO_2022_v1_15s_bed_elev"


def download_grid(
    output: Path,
    step: float = 0.1,
    west: float = -51.0,
    east: float = -35.0,
    south: float = 20.0,
    north: float = 30.0,
) -> pd.DataFrame:
    width = int(round((east - west) / step)) + 1
    height = int(round((north - south) / step)) + 1

    # 픽셀 중심이 정확히 -51.0, -50.9, ...에 오도록 bbox를 반 칸 확장한다.
    bbox = (west - step / 2, south - step / 2,
            east + step / 2, north + step / 2)
    mosaic_rule = {
        "mosaicMethod": "esriMosaicLockRaster",
        "lockRasterIds": [ETOPO_BED_RASTER_ID],
        "mosaicOperation": "MT_FIRST",
    }
    params = {
        "bbox": ",".join(f"{v:.8f}" for v in bbox),
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": f"{width},{height}",
        "format": "tiff",
        "pixelType": "F32",
        "interpolation": "RSP_Bilinear",
        "mosaicRule": json.dumps(mosaic_rule, separators=(",", ":")),
        "f": "json",
    }
    request_url = f"{SERVICE}/exportImage?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(request_url, timeout=120) as response:
        export_info = json.load(response)
    if "href" not in export_info:
        raise RuntimeError(f"ETOPO exportImage 실패: {export_info}")

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        with urllib.request.urlopen(export_info["href"], timeout=120) as response:
            tmp.write(response.read())

    try:
        with rasterio.open(tmp_path) as src:
            depth = src.read(1).astype(float)
            rows, cols = np.indices(depth.shape)
            xs, ys = rasterio.transform.xy(src.transform, rows, cols, offset="center")
        frame = pd.DataFrame({
            "lon": np.asarray(xs).ravel(),
            "lat": np.asarray(ys).ravel(),
            "depth_m": depth.ravel(),
        })
    finally:
        tmp_path.unlink(missing_ok=True)

    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=["depth_m"])
    frame["lon"] = frame["lon"].round(6)
    frame["lat"] = frame["lat"].round(6)
    frame["depth_m"] = frame["depth_m"].round(2)
    frame["source"] = SOURCE_NAME
    frame = frame.sort_values(["lat", "lon"]).reset_index(drop=True)

    expected = width * height
    if len(frame) != expected:
        raise RuntimeError(f"격자점 수 불일치: expected={expected}, received={len(frame)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=float, default=0.1, help="격자 간격(도), 기본 0.1")
    parser.add_argument("--west", type=float, default=-51.0)
    parser.add_argument("--east", type=float, default=-35.0)
    parser.add_argument("--south", type=float, default=20.0)
    parser.add_argument("--north", type=float, default=30.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "data" / "real_bathymetry_grid.csv",
    )
    args = parser.parse_args()
    if not (args.west < args.east and args.south < args.north):
        parser.error("west < east, south < north 이어야 합니다.")
    frame = download_grid(
        args.output, args.step, args.west, args.east, args.south, args.north
    )
    print(
        f"저장 완료: {args.output} ({len(frame):,}점, {args.step:.3f}° 간격, "
        f"수심 {frame.depth_m.min():.1f}~{frame.depth_m.max():.1f} m)"
    )


if __name__ == "__main__":
    main()
