# -*- coding: utf-8 -*-
"""NOAA EMAG2v3 ImageServer에서 광역 고지자기 이상 격자를 내려받는다."""

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

SERVICE = "https://gis.ngdc.noaa.gov/arcgis/rest/services/EMAG2v3/ImageServer"


def download(output: Path, west: float, east: float, south: float,
             north: float, step: float) -> pd.DataFrame:
    width = int(round((east - west) / step)) + 1
    height = int(round((north - south) / step)) + 1
    bbox = (west - step / 2, south - step / 2,
            east + step / 2, north + step / 2)
    params = {
        "bbox": ",".join(f"{v:.8f}" for v in bbox),
        "bboxSR": "4326", "imageSR": "4326",
        "size": f"{width},{height}", "format": "tiff",
        "pixelType": "F32", "interpolation": "RSP_Bilinear", "f": "json",
    }
    url = f"{SERVICE}/exportImage?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=120) as response:
        info = json.load(response)
    if "href" not in info:
        raise RuntimeError(f"EMAG2 export 실패: {info}")
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        with urllib.request.urlopen(info["href"], timeout=120) as response:
            tmp.write(response.read())
    try:
        with rasterio.open(tmp_path) as src:
            values = src.read(1).astype(float)
            rows, cols = np.indices(values.shape)
            xs, ys = rasterio.transform.xy(src.transform, rows, cols, offset="center")
    finally:
        tmp_path.unlink(missing_ok=True)
    frame = pd.DataFrame({
        "lon": np.asarray(xs).ravel(), "lat": np.asarray(ys).ravel(),
        "anomaly_nT": values.ravel(),
    }).replace([np.inf, -np.inf, 99999], np.nan).dropna()
    frame["lon"] = frame["lon"].round(6)
    frame["lat"] = frame["lat"].round(6)
    frame["anomaly_nT"] = frame["anomaly_nT"].round(3)
    frame["source"] = "NOAA_EMAG2v3"
    frame = frame.sort_values(["lat", "lon"]).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"저장 완료: {output} ({len(frame):,}점, {step}° 간격)")
    return frame


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--west", type=float, default=-55)
    p.add_argument("--east", type=float, default=-25)
    p.add_argument("--south", type=float, default=10)
    p.add_argument("--north", type=float, default=40)
    p.add_argument("--step", type=float, default=0.1)
    p.add_argument("--output", type=Path,
                   default=Path(__file__).parent / "data" / "regional_magnetic_anomaly.csv")
    a = p.parse_args()
    download(a.output, a.west, a.east, a.south, a.north, a.step)


if __name__ == "__main__":
    main()
